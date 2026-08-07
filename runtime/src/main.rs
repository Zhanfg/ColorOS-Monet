// SPDX-License-Identifier: Apache-2.0

use anyhow::{anyhow, bail, Context, Result};
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::ffi::OsStr;
use std::fs::{self, File};
use std::io::{Cursor, Read, Seek, SeekFrom, Write};
use std::os::unix::fs::PermissionsExt;
use std::path::{Component, Path, PathBuf};
use std::process::{Command, Output};
use std::thread;
use std::time::Duration;
use tar::{Archive, Builder, EntryType};
use tempfile::TempDir;
use walkdir::WalkDir;

const MAGIC: &[u8; 8] = b"CMONET01";
const FORMAT_VERSION: u16 = 1;
const HEADER_SIZE: usize = 128;
const FLAG_ZSTD_TAR: u32 = 1;
const DEFAULT_STORE: &str = "/data/adb/coloros-monet/components";
const DEFAULT_RUNTIME_DIR: &str = "/data/adb/coloros-monet/runtime";
const APPLIED_FILE: &str = "applied-overlays.txt";
const TYPE_INT_DEC: &str = "0x10";
const TYPE_INT_BOOLEAN: &str = "0x12";
const TYPE_DIMENSION: &str = "0x05";
const TYPE_FILE: &str = "4294967295";

#[derive(Parser, Debug)]
#[command(
    name = "monetctl",
    version,
    about = "APK-free ColorOS Monet component manager"
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Build a .cmonet component package from a source directory.
    Pack { source: PathBuf, output: PathBuf },
    /// Print component metadata as JSON.
    Inspect { package: PathBuf },
    /// Verify package header, payload, and manifest digests.
    Verify { package: PathBuf },
    /// Install one component package into the persistent store.
    Install {
        package: PathBuf,
        #[arg(long, default_value = DEFAULT_STORE)]
        store: PathBuf,
    },
    /// Install every .cmonet file in a directory and initialize new defaults.
    Sync {
        directory: PathBuf,
        #[arg(long, default_value = DEFAULT_STORE)]
        store: PathBuf,
        #[arg(long)]
        enable_defaults: bool,
    },
    /// Enable one installed component and apply it immediately.
    Enable {
        id: String,
        #[arg(long, default_value = DEFAULT_STORE)]
        store: PathBuf,
    },
    /// Disable one installed component.
    Disable {
        id: String,
        #[arg(long, default_value = DEFAULT_STORE)]
        store: PathBuf,
    },
    /// Disable every installed component.
    DisableAll {
        #[arg(long, default_value = DEFAULT_STORE)]
        store: PathBuf,
    },
    /// Apply every enabled component.
    ApplyAll {
        #[arg(long, default_value = DEFAULT_STORE)]
        store: PathBuf,
    },
    /// List installed components and enabled state as JSON.
    List {
        #[arg(long, default_value = DEFAULT_STORE)]
        store: PathBuf,
    },
    /// Print a stable fingerprint of the current Android theme palette.
    Fingerprint,
    /// Watch the palette fingerprint and reapply enabled components on change.
    Watch {
        #[arg(long, default_value = DEFAULT_STORE)]
        store: PathBuf,
        #[arg(long, default_value = DEFAULT_RUNTIME_DIR)]
        runtime_dir: PathBuf,
        #[arg(long, default_value_t = 20)]
        interval_seconds: u64,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "kebab-case")]
enum Backend {
    /// APK-free fabricated overlay built through Android's OverlayManager shell API.
    FabricatedOverlay,
    /// Compatibility backend reserved for firmware that rejects fabricated overlays.
    SystemlessRro,
    /// Future resource-hook backend for targets protected by overlayable policy.
    ZygiskResource,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ComponentManifest {
    schema: u32,
    id: String,
    name: String,
    version: String,
    target_package: String,
    overlay_name: String,
    backend: Backend,
    resources: String,
    #[serde(default)]
    target_overlayable: Option<String>,
    #[serde(default)]
    min_sdk: Option<u32>,
    #[serde(default)]
    description: Option<String>,
    #[serde(default)]
    inspiration: Option<String>,
    #[serde(default)]
    source_status: Option<String>,
    #[serde(default)]
    category: Option<String>,
    #[serde(default)]
    exclusive_group: Option<String>,
    #[serde(default)]
    default_enabled: bool,
    #[serde(default)]
    tags: Vec<String>,
}

#[derive(Debug, Clone)]
struct Header {
    version: u16,
    flags: u32,
    manifest_len: u64,
    payload_len: u64,
    manifest_sha256: [u8; 32],
    payload_sha256: [u8; 32],
}

#[derive(Debug, Serialize, Deserialize, Default)]
struct State {
    enabled: BTreeMap<String, bool>,
}

#[derive(Debug, Serialize)]
struct ComponentStatus {
    manifest: ComponentManifest,
    enabled: bool,
    target_installed: bool,
}

#[derive(Debug, Clone)]
struct ResourceRow {
    resource_type: String,
    resource_name: String,
    value: String,
    config: Option<String>,
}

fn main() {
    if let Err(error) = run() {
        eprintln!("error: {error:#}");
        std::process::exit(1);
    }
}

fn run() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Pack { source, output } => pack_component(&source, &output),
        Commands::Inspect { package } => {
            let (_, manifest, _) = read_package(&package)?;
            println!("{}", serde_json::to_string_pretty(&manifest)?);
            Ok(())
        }
        Commands::Verify { package } => {
            let (header, manifest, _) = read_package(&package)?;
            println!(
                "verified id={} version={} format={} payload_bytes={}",
                manifest.id, manifest.version, header.version, header.payload_len
            );
            Ok(())
        }
        Commands::Install { package, store } => {
            let manifest = install_component(&package, &store)?;
            println!("installed {} {}", manifest.id, manifest.version);
            Ok(())
        }
        Commands::Sync {
            directory,
            store,
            enable_defaults,
        } => sync_components(&directory, &store, enable_defaults),
        Commands::Enable { id, store } => enable_component(&store, &id),
        Commands::Disable { id, store } => disable_component(&store, &id),
        Commands::DisableAll { store } => disable_all(&store),
        Commands::ApplyAll { store } => apply_all(&store),
        Commands::List { store } => list_components(&store),
        Commands::Fingerprint => {
            println!("{}", theme_fingerprint()?);
            Ok(())
        }
        Commands::Watch {
            store,
            runtime_dir,
            interval_seconds,
        } => watch_theme(&store, &runtime_dir, interval_seconds),
    }
}

fn pack_component(source: &Path, output: &Path) -> Result<()> {
    let manifest_path = source.join("component.json");
    let manifest_bytes =
        fs::read(&manifest_path).with_context(|| format!("read {}", manifest_path.display()))?;
    let manifest: ComponentManifest = serde_json::from_slice(&manifest_bytes)
        .with_context(|| format!("parse {}", manifest_path.display()))?;
    validate_manifest(&manifest)?;

    let resource_path = source.join(&manifest.resources);
    if !resource_path.is_file() {
        bail!("resource table does not exist: {}", resource_path.display());
    }
    let _ = read_resource_rows(&resource_path)?;

    let encoder = zstd::Encoder::new(Vec::new(), 12)?;
    let mut tar = Builder::new(encoder);
    tar.mode(tar::HeaderMode::Deterministic);
    for entry in WalkDir::new(source).follow_links(false) {
        let entry = entry?;
        let path = entry.path();
        if path == manifest_path || path == source {
            continue;
        }
        let relative = path.strip_prefix(source)?;
        validate_relative_path(relative)?;
        if entry.file_type().is_symlink() {
            bail!(
                "component source must not contain symlinks: {}",
                path.display()
            );
        }
        if entry.file_type().is_dir() {
            tar.append_dir(relative, path)?;
        } else if entry.file_type().is_file() {
            tar.append_path_with_name(path, relative)?;
        }
    }
    let encoder = tar.into_inner()?;
    let payload = encoder.finish()?;

    let manifest_hash: [u8; 32] = Sha256::digest(&manifest_bytes).into();
    let payload_hash: [u8; 32] = Sha256::digest(&payload).into();
    let header = Header {
        version: FORMAT_VERSION,
        flags: FLAG_ZSTD_TAR,
        manifest_len: manifest_bytes.len() as u64,
        payload_len: payload.len() as u64,
        manifest_sha256: manifest_hash,
        payload_sha256: payload_hash,
    };

    if let Some(parent) = output.parent() {
        fs::create_dir_all(parent)?;
    }
    let mut file = File::create(output)?;
    write_header(&mut file, &header)?;
    file.write_all(&manifest_bytes)?;
    file.write_all(&payload)?;
    file.sync_all()?;
    println!("packed {} -> {}", manifest.id, output.display());
    Ok(())
}

fn install_component(package: &Path, store: &Path) -> Result<ComponentManifest> {
    let (_, manifest, payload) = read_package(package)?;
    let component_dir = store.join(&manifest.id);
    let version_dir = component_dir.join(&manifest.version);
    let stage_dir = component_dir.join(format!(".stage-{}", std::process::id()));
    if stage_dir.exists() {
        fs::remove_dir_all(&stage_dir)?;
    }
    fs::create_dir_all(&stage_dir)?;
    fs::write(
        stage_dir.join("component.json"),
        serde_json::to_vec_pretty(&manifest)?,
    )?;

    let decoder = zstd::Decoder::new(Cursor::new(payload))?;
    let mut archive = Archive::new(decoder);
    for item in archive.entries()? {
        let mut item = item?;
        let path = item.path()?.into_owned();
        validate_relative_path(&path)?;
        let kind = item.header().entry_type();
        if kind != EntryType::Regular && kind != EntryType::Directory {
            bail!(
                "component archive contains unsupported entry type at {}",
                path.display()
            );
        }
        item.unpack_in(&stage_dir)?;
    }

    if version_dir.exists() {
        fs::remove_dir_all(&version_dir)?;
    }
    fs::create_dir_all(&component_dir)?;
    fs::rename(&stage_dir, &version_dir)?;
    fs::write(component_dir.join("current"), manifest.version.as_bytes())?;

    for entry in fs::read_dir(&component_dir)? {
        let entry = entry?;
        if !entry.file_type()?.is_dir() {
            continue;
        }
        let name = entry.file_name();
        let name = name.to_string_lossy();
        if name != manifest.version && !name.starts_with(".stage-") {
            let _ = fs::remove_dir_all(entry.path());
        }
    }
    Ok(manifest)
}

fn sync_components(directory: &Path, store: &Path, enable_defaults: bool) -> Result<()> {
    if !directory.is_dir() {
        bail!(
            "component package directory does not exist: {}",
            directory.display()
        );
    }
    fs::create_dir_all(store)?;
    let mut state = read_state(store)?;
    let mut packages: Vec<PathBuf> = fs::read_dir(directory)?
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.path())
        .filter(|path| path.extension() == Some(OsStr::new("cmonet")))
        .collect();
    packages.sort();
    if packages.is_empty() {
        bail!("no .cmonet packages found in {}", directory.display());
    }

    let mut installed = 0usize;
    for package in packages {
        let (_, preview, _) = read_package(&package)?;
        let new_component = !state.enabled.contains_key(&preview.id);
        let manifest = install_component(&package, store)?;
        if new_component {
            let enabled = enable_defaults
                && manifest.default_enabled
                && package_installed(&manifest.target_package);
            state.enabled.insert(manifest.id.clone(), enabled);
        }
        installed += 1;
    }
    normalize_exclusive_defaults(store, &mut state)?;
    write_state(store, &state)?;
    println!("synchronized {installed} component package(s)");
    Ok(())
}

fn normalize_exclusive_defaults(store: &Path, state: &mut State) -> Result<()> {
    let mut selected: BTreeSet<String> = BTreeSet::new();
    let ids: Vec<String> = state.enabled.keys().cloned().collect();
    for id in ids {
        if !state.enabled.get(&id).copied().unwrap_or(false) {
            continue;
        }
        let (manifest, _) = load_installed(store, &id)?;
        if let Some(group) = manifest.exclusive_group {
            if !selected.insert(group) {
                state.enabled.insert(id, false);
            }
        }
    }
    Ok(())
}

fn enable_component(store: &Path, id: &str) -> Result<()> {
    validate_component_id(id)?;
    let (manifest, _) = load_installed(store, id)?;
    if !package_installed(&manifest.target_package) {
        bail!(
            "target package {} is not installed",
            manifest.target_package
        );
    }

    let mut state = read_state(store)?;
    if let Some(group) = &manifest.exclusive_group {
        let other_ids: Vec<String> = state
            .enabled
            .iter()
            .filter_map(|(candidate, enabled)| {
                if *enabled && candidate != id {
                    Some(candidate.clone())
                } else {
                    None
                }
            })
            .collect();
        for candidate in other_ids {
            if let Ok((other, _)) = load_installed(store, &candidate) {
                if other.exclusive_group.as_deref() == Some(group.as_str()) {
                    let _ = disable_overlay_set(store, &candidate);
                    state.enabled.insert(candidate, false);
                }
            }
        }
    }
    state.enabled.insert(id.to_string(), true);
    write_state(store, &state)?;
    apply_component(store, id)
}

fn disable_component(store: &Path, id: &str) -> Result<()> {
    validate_component_id(id)?;
    let _ = load_installed(store, id)?;
    disable_overlay_set(store, id)?;
    let mut state = read_state(store)?;
    state.enabled.insert(id.to_string(), false);
    write_state(store, &state)
}

fn disable_all(store: &Path) -> Result<()> {
    let mut state = read_state(store)?;
    let ids: Vec<String> = state.enabled.keys().cloned().collect();
    for id in ids {
        let _ = disable_overlay_set(store, &id);
        state.enabled.insert(id, false);
    }
    write_state(store, &state)?;
    println!("disabled all components");
    Ok(())
}

fn apply_all(store: &Path) -> Result<()> {
    let state = read_state(store)?;
    let mut failures = 0usize;
    for (id, enabled) in state.enabled {
        if enabled {
            if let Err(error) = apply_component(store, &id) {
                failures += 1;
                eprintln!("component {id}: {error:#}");
            }
        }
    }
    if failures > 0 {
        bail!("{failures} enabled component(s) failed");
    }
    Ok(())
}

fn apply_component(store: &Path, id: &str) -> Result<()> {
    let (manifest, version_dir) = load_installed(store, id)?;
    if !package_installed(&manifest.target_package) {
        println!(
            "skipped {}: target {} is not installed",
            manifest.id, manifest.target_package
        );
        return Ok(());
    }
    if let Some(min_sdk) = manifest.min_sdk {
        let sdk = getprop_u32("ro.build.version.sdk").unwrap_or_default();
        if sdk < min_sdk {
            bail!("component requires SDK {min_sdk}, device has {sdk}");
        }
    }
    match manifest.backend {
        Backend::FabricatedOverlay => apply_fabricated_overlay(store, &manifest, &version_dir),
        Backend::SystemlessRro => bail!(
            "systemless-rro is reserved as a compatibility fallback and is not emitted by runtime v2"
        ),
        Backend::ZygiskResource => bail!("zygisk-resource backend is not implemented yet"),
    }
}

fn apply_fabricated_overlay(
    store: &Path,
    manifest: &ComponentManifest,
    version_dir: &Path,
) -> Result<()> {
    ensure_root()?;
    let mut rows = read_resource_rows(&version_dir.join(&manifest.resources))?;
    if rows.is_empty() {
        bail!("component has no resource rows");
    }
    rows.sort_by(|left, right| {
        (&left.resource_type, &left.resource_name, &left.config).cmp(&(
            &right.resource_type,
            &right.resource_name,
            &right.config,
        ))
    });

    disable_overlay_set(store, &manifest.id)?;
    let scratch = create_scratch_dir()?;
    let mut applied = Vec::<String>::new();

    let primary: Vec<ResourceRow> = rows
        .iter()
        .filter(|row| {
            (row.resource_type == "string" && !row.value.starts_with("file:"))
                || (row.resource_type == "color" && !row.value.starts_with("file:"))
                || (row.resource_type == "drawable" && row.value.starts_with("file:"))
        })
        .cloned()
        .collect();
    if !primary.is_empty() {
        let mut xml = String::from("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<overlay>\n");
        for row in &primary {
            let value = resolve_primary_value(row, version_dir, scratch.path())?;
            xml.push_str("  <item target=\"");
            xml.push_str(&xml_escape(&format!(
                "{}/{}",
                row.resource_type, row.resource_name
            )));
            xml.push_str("\" value=\"");
            xml.push_str(&xml_escape(&value));
            xml.push('"');
            if let Some(config) = normalized_config(row.config.as_deref()) {
                xml.push_str(" config=\"");
                xml.push_str(&xml_escape(config));
                xml.push('"');
            }
            xml.push_str(" />\n");
        }
        xml.push_str("</overlay>\n");
        let xml_path = scratch.path().join("overlay.xml");
        fs::write(&xml_path, xml.as_bytes())?;
        fs::set_permissions(&xml_path, fs::Permissions::from_mode(0o644))?;

        let mut args = fabricate_prefix(manifest);
        args.extend([
            "--file".to_string(),
            xml_path.to_string_lossy().into_owned(),
        ]);
        if let Err(error) = run_cmd_owned("cmd", &args) {
            rollback_identifiers(&applied);
            return Err(error).context("register multi-resource fabricated overlay");
        }
        let identifier = fabricated_identifier(&manifest.overlay_name);
        if let Err(error) = enable_identifier(&identifier) {
            rollback_identifiers(&applied);
            return Err(error).context("enable multi-resource fabricated overlay");
        }
        applied.push(identifier);
    }

    for row in rows.iter().filter(|row| {
        !((row.resource_type == "string" && !row.value.starts_with("file:"))
            || (row.resource_type == "color" && !row.value.starts_with("file:"))
            || (row.resource_type == "drawable" && row.value.starts_with("file:")))
    }) {
        let (type_id, encoded_value) = if row.value.starts_with("file:") {
            (
                TYPE_FILE,
                stage_file_value(row, version_dir, scratch.path())?,
            )
        } else {
            let (kind, value) = encode_scalar_row(row)?;
            (kind, value)
        };
        let overlay_name = scalar_overlay_name(manifest, row);
        let mut args = fabricate_prefix_with_name(manifest, &overlay_name);
        if let Some(config) = normalized_config(row.config.as_deref()) {
            args.push("--config".to_string());
            args.push(config.to_string());
        }
        args.extend([
            format!(
                "{}:{}/{}",
                manifest.target_package, row.resource_type, row.resource_name
            ),
            type_id.to_string(),
            encoded_value,
        ]);
        if let Err(error) = run_cmd_owned("cmd", &args) {
            rollback_identifiers(&applied);
            return Err(error).with_context(|| {
                format!(
                    "register scalar fabricated overlay for {}/{}",
                    row.resource_type, row.resource_name
                )
            });
        }
        let identifier = fabricated_identifier(&overlay_name);
        if let Err(error) = enable_identifier(&identifier) {
            rollback_identifiers(&applied);
            return Err(error).context("enable scalar fabricated overlay");
        }
        applied.push(identifier);
    }

    write_applied_identifiers(store, &manifest.id, &applied)?;
    println!(
        "applied {} using {} fabricated overlay object(s)",
        manifest.id,
        applied.len()
    );
    Ok(())
}

fn fabricate_prefix(manifest: &ComponentManifest) -> Vec<String> {
    fabricate_prefix_with_name(manifest, &manifest.overlay_name)
}

fn fabricate_prefix_with_name(manifest: &ComponentManifest, name: &str) -> Vec<String> {
    let mut args = vec![
        "overlay".to_string(),
        "fabricate".to_string(),
        "--user".to_string(),
        "0".to_string(),
    ];
    if let Some(target_name) = &manifest.target_overlayable {
        args.push("--target-name".to_string());
        args.push(target_name.clone());
    }
    args.extend([
        "--target".to_string(),
        manifest.target_package.clone(),
        "--name".to_string(),
        name.to_string(),
    ]);
    args
}

fn scalar_overlay_name(manifest: &ComponentManifest, row: &ResourceRow) -> String {
    let input = format!(
        "{}\0{}\0{}",
        row.resource_type,
        row.resource_name,
        row.config.as_deref().unwrap_or("")
    );
    let digest = hex::encode(Sha256::digest(input.as_bytes()));
    format!("{}_{}", manifest.overlay_name, &digest[..12])
}

fn encode_scalar_row(row: &ResourceRow) -> Result<(&'static str, String)> {
    match row.resource_type.as_str() {
        "bool" => match row.value.as_str() {
            "true" | "1" => Ok((TYPE_INT_BOOLEAN, "1".to_string())),
            "false" | "0" => Ok((TYPE_INT_BOOLEAN, "0".to_string())),
            _ => bail!("invalid boolean value {}", row.value),
        },
        "integer" => {
            let value = parse_u32(&row.value)?;
            Ok((TYPE_INT_DEC, value.to_string()))
        }
        "dimen" => Ok((
            TYPE_DIMENSION,
            format!("0x{:08x}", encode_dimension(&row.value)?),
        )),
        other => bail!("resource type {other} is not supported by the fabricated-overlay backend"),
    }
}

fn encode_dimension(raw: &str) -> Result<u32> {
    let raw = raw.trim();
    let units = [
        ("dip", 1u32),
        ("dp", 1u32),
        ("sp", 2u32),
        ("px", 0u32),
        ("pt", 3u32),
        ("in", 4u32),
        ("mm", 5u32),
    ];
    let mut number = raw;
    let mut unit = 0u32;
    for (suffix, code) in units {
        if let Some(prefix) = raw.strip_suffix(suffix) {
            number = prefix;
            unit = code;
            break;
        }
    }
    let value: f64 = number
        .trim()
        .parse()
        .with_context(|| format!("invalid dimension {raw}"))?;
    if !value.is_finite() {
        bail!("dimension is not finite: {raw}");
    }

    let candidates = [
        (3u32, 8_388_608.0f64),
        (2u32, 32_768.0f64),
        (1u32, 128.0f64),
        (0u32, 1.0f64),
    ];
    for (radix, scale) in candidates {
        let mantissa = (value * scale).round();
        if (-8_388_608.0..=8_388_607.0).contains(&mantissa) {
            let mantissa = mantissa as i32;
            let encoded = ((mantissa as u32) & 0x00ff_ffff) << 8;
            return Ok(encoded | (radix << 4) | unit);
        }
    }
    bail!("dimension is outside Android complex-value range: {raw}")
}

fn create_scratch_dir() -> Result<TempDir> {
    let root = Path::new("/data/local/tmp");
    if root.is_dir() {
        TempDir::new_in(root).context("create /data/local/tmp scratch directory")
    } else {
        TempDir::new().context("create scratch directory")
    }
}

fn stage_file_value(row: &ResourceRow, version_dir: &Path, scratch_dir: &Path) -> Result<String> {
    let relative = row
        .value
        .strip_prefix("file:")
        .ok_or_else(|| anyhow!("resource value is not a file reference"))?;
    let relative = Path::new(relative);
    validate_relative_path(relative)?;
    let absolute = version_dir.join(relative);
    if !absolute.is_file() {
        bail!(
            "component file resource does not exist: {}",
            absolute.display()
        );
    }
    let identity = format!(
        "{}\0{}\0{}",
        row.resource_type,
        row.resource_name,
        row.config.as_deref().unwrap_or("")
    );
    let digest = hex::encode(Sha256::digest(identity.as_bytes()));
    let extension = absolute
        .extension()
        .and_then(OsStr::to_str)
        .unwrap_or("bin");
    let staged = scratch_dir.join(format!("asset-{}.{}", &digest[..16], extension));
    fs::copy(&absolute, &staged)?;
    fs::set_permissions(&staged, fs::Permissions::from_mode(0o644))?;
    Ok(staged.to_string_lossy().into_owned())
}

fn resolve_primary_value(
    row: &ResourceRow,
    version_dir: &Path,
    scratch_dir: &Path,
) -> Result<String> {
    let value = row.value.as_str();
    if let Some(name) = value.strip_prefix("@android:color/") {
        return lookup_android_color(name);
    }
    if let Some(raw) = value.strip_prefix("argb:") {
        if raw.len() != 8 || !raw.bytes().all(|byte| byte.is_ascii_hexdigit()) {
            bail!("argb value must contain exactly eight hexadecimal digits: {value}");
        }
        return Ok(format!("0x{}", raw.to_ascii_lowercase()));
    }
    if value.starts_with("file:") {
        if row.resource_type != "drawable" {
            bail!("multi-entry XML accepts file resources only for drawable targets");
        }
        return stage_file_value(row, version_dir, scratch_dir);
    }
    if value.starts_with("0x") {
        let _ = parse_u32(value)?;
        return Ok(value.to_ascii_lowercase());
    }
    if let Some(hex) = value.strip_prefix('#') {
        let normalized = match hex.len() {
            6 => format!("0xff{hex}"),
            8 => format!("0x{hex}"),
            _ => bail!("expected #RRGGBB or #AARRGGBB, got {value}"),
        };
        let _ = parse_u32(&normalized)?;
        return Ok(normalized.to_ascii_lowercase());
    }
    if let Some(text) = value.strip_prefix("string:") {
        return Ok(text.to_string());
    }
    if row.resource_type == "string" {
        return Ok(value.to_string());
    }
    bail!("unsupported primary resource value {value}")
}

fn normalized_config(config: Option<&str>) -> Option<&str> {
    match config {
        Some("") | None => None,
        Some(value) => Some(value),
    }
}

fn enable_identifier(identifier: &str) -> Result<()> {
    run_cmd("cmd", ["overlay", "enable", "--user", "0", identifier])
}

fn rollback_identifiers(identifiers: &[String]) {
    for identifier in identifiers.iter().rev() {
        let _ = run_cmd("cmd", ["overlay", "disable", "--user", "0", identifier]);
    }
}

fn disable_overlay_set(store: &Path, id: &str) -> Result<()> {
    validate_component_id(id)?;
    let component_dir = store.join(id);
    let applied_path = component_dir.join(APPLIED_FILE);
    if let Ok(text) = fs::read_to_string(&applied_path) {
        for identifier in text.lines().map(str::trim).filter(|line| !line.is_empty()) {
            let _ = run_cmd("cmd", ["overlay", "disable", "--user", "0", identifier]);
        }
    } else if let Ok((manifest, _)) = load_installed(store, id) {
        let identifier = fabricated_identifier(&manifest.overlay_name);
        let _ = run_cmd("cmd", ["overlay", "disable", "--user", "0", &identifier]);
    }
    let _ = fs::remove_file(applied_path);
    Ok(())
}

fn write_applied_identifiers(store: &Path, id: &str, identifiers: &[String]) -> Result<()> {
    let path = store.join(id).join(APPLIED_FILE);
    let mut text = identifiers.join("\n");
    if !text.is_empty() {
        text.push('\n');
    }
    fs::write(path, text)?;
    Ok(())
}

fn fabricated_identifier(name: &str) -> String {
    format!("com.android.shell:{name}")
}

fn lookup_android_color(name: &str) -> Result<String> {
    let resource = format!("android:color/{name}");
    let output = run_output("cmd", ["overlay", "lookup", "android", &resource])?;
    let stdout = String::from_utf8_lossy(&output.stdout);
    for token in stdout.split_whitespace().rev() {
        let token = token.trim_matches(|character: char| {
            !character.is_ascii_hexdigit() && character != 'x' && character != '#'
        });
        if let Some(hex) = token.strip_prefix("0x") {
            if (6..=8).contains(&hex.len()) && hex.bytes().all(|byte| byte.is_ascii_hexdigit()) {
                let value = u32::from_str_radix(hex, 16)?;
                let value = if hex.len() == 6 {
                    value | 0xff00_0000
                } else {
                    value
                };
                return Ok(format!("0x{value:08x}"));
            }
        }
        if let Some(hex) = token.strip_prefix('#') {
            if (hex.len() == 6 || hex.len() == 8)
                && hex.bytes().all(|byte| byte.is_ascii_hexdigit())
            {
                let prefix = if hex.len() == 6 { "ff" } else { "" };
                return Ok(format!("0x{prefix}{hex}").to_ascii_lowercase());
            }
        }
    }
    bail!("lookup {resource} returned no ARGB value: {stdout}")
}

fn list_components(store: &Path) -> Result<()> {
    let state = read_state(store)?;
    let mut statuses = Vec::new();
    if store.exists() {
        for entry in fs::read_dir(store)? {
            let entry = entry?;
            if !entry.file_type()?.is_dir() {
                continue;
            }
            let id = entry.file_name().to_string_lossy().into_owned();
            if let Ok((manifest, _)) = load_installed(store, &id) {
                statuses.push(ComponentStatus {
                    enabled: state.enabled.get(&id).copied().unwrap_or(false),
                    target_installed: package_installed(&manifest.target_package),
                    manifest,
                });
            }
        }
    }
    statuses.sort_by(|left, right| left.manifest.id.cmp(&right.manifest.id));
    println!("{}", serde_json::to_string_pretty(&statuses)?);
    Ok(())
}

fn load_installed(store: &Path, id: &str) -> Result<(ComponentManifest, PathBuf)> {
    validate_component_id(id)?;
    let component_dir = store.join(id);
    let version = fs::read_to_string(component_dir.join("current"))
        .with_context(|| format!("component {id} is not installed"))?;
    let version = version.trim();
    validate_version(version)?;
    let version_dir = component_dir.join(version);
    let manifest: ComponentManifest =
        serde_json::from_slice(&fs::read(version_dir.join("component.json"))?)?;
    validate_manifest(&manifest)?;
    if manifest.id != id || manifest.version != version {
        bail!("installed component metadata does not match store path");
    }
    Ok((manifest, version_dir))
}

fn read_state(store: &Path) -> Result<State> {
    let path = store.join("state.json");
    if !path.exists() {
        return Ok(State::default());
    }
    Ok(serde_json::from_slice(&fs::read(path)?)?)
}

fn write_state(store: &Path, state: &State) -> Result<()> {
    fs::create_dir_all(store)?;
    let path = store.join("state.json");
    let temporary = store.join("state.json.tmp");
    fs::write(&temporary, serde_json::to_vec_pretty(state)?)?;
    fs::rename(temporary, path)?;
    Ok(())
}

fn read_resource_rows(path: &Path) -> Result<Vec<ResourceRow>> {
    let text = fs::read_to_string(path).with_context(|| format!("read {}", path.display()))?;
    let mut rows = Vec::new();
    for (index, line) in text.lines().enumerate() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let fields: Vec<_> = line.split('\t').collect();
        if !(3..=4).contains(&fields.len()) {
            bail!(
                "{}:{} expected 3 or 4 tab-separated fields",
                path.display(),
                index + 1
            );
        }
        validate_resource_identifier(fields[0], fields[1]).with_context(|| {
            format!(
                "{}:{} invalid resource identifier",
                path.display(),
                index + 1
            )
        })?;
        rows.push(ResourceRow {
            resource_type: fields[0].to_string(),
            resource_name: fields[1].to_string(),
            value: fields[2].to_string(),
            config: fields.get(3).map(|value| value.to_string()),
        });
    }
    Ok(rows)
}

fn read_package(path: &Path) -> Result<(Header, ComponentManifest, Vec<u8>)> {
    let metadata = fs::metadata(path)?;
    if metadata.len() < HEADER_SIZE as u64 {
        bail!("component package is smaller than its header");
    }
    let mut file = File::open(path)?;
    let header = read_header(&mut file)?;
    if header.version != FORMAT_VERSION {
        bail!("unsupported format version {}", header.version);
    }
    if header.flags & FLAG_ZSTD_TAR == 0 {
        bail!("component payload is not zstd tar");
    }
    let expected = HEADER_SIZE as u64 + header.manifest_len + header.payload_len;
    if metadata.len() != expected {
        bail!(
            "component length mismatch: header describes {expected} bytes, file has {}",
            metadata.len()
        );
    }
    if header.manifest_len > 1024 * 1024 || header.payload_len > 256 * 1024 * 1024 {
        bail!("component package exceeds safety limits");
    }
    let mut manifest_bytes = vec![0u8; header.manifest_len as usize];
    file.read_exact(&mut manifest_bytes)?;
    let mut payload = vec![0u8; header.payload_len as usize];
    file.read_exact(&mut payload)?;
    let manifest_digest: [u8; 32] = Sha256::digest(&manifest_bytes).into();
    let payload_digest: [u8; 32] = Sha256::digest(&payload).into();
    if manifest_digest != header.manifest_sha256 {
        bail!("manifest digest mismatch");
    }
    if payload_digest != header.payload_sha256 {
        bail!("payload digest mismatch");
    }
    let manifest: ComponentManifest = serde_json::from_slice(&manifest_bytes)?;
    validate_manifest(&manifest)?;
    Ok((header, manifest, payload))
}

fn validate_manifest(manifest: &ComponentManifest) -> Result<()> {
    if manifest.schema != 1 {
        bail!("unsupported manifest schema {}", manifest.schema);
    }
    validate_component_id(&manifest.id)?;
    validate_version(&manifest.version)?;
    if manifest.name.trim().is_empty() {
        bail!("component name is required");
    }
    validate_package_name(&manifest.target_package)?;
    if manifest.overlay_name.is_empty()
        || manifest.overlay_name.len() > 100
        || !manifest
            .overlay_name
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'_')
    {
        bail!(
            "overlay_name must use at most 100 lowercase ASCII characters, digits, and underscores"
        );
    }
    if let Some(group) = &manifest.exclusive_group {
        validate_component_id(group)?;
    }
    let resources = Path::new(&manifest.resources);
    validate_relative_path(resources)?;
    Ok(())
}

fn validate_component_id(id: &str) -> Result<()> {
    if id.is_empty()
        || id.len() > 96
        || !id
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'-')
    {
        bail!("component id must use at most 96 lowercase ASCII characters, digits, and hyphens");
    }
    Ok(())
}

fn validate_version(version: &str) -> Result<()> {
    if version.is_empty()
        || version.len() > 64
        || !version
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'-' | b'_' | b'+'))
    {
        bail!("version contains unsupported characters");
    }
    Ok(())
}

fn validate_package_name(package: &str) -> Result<()> {
    if package.is_empty()
        || package.starts_with('.')
        || package.ends_with('.')
        || package.split('.').any(|part| {
            part.is_empty()
                || !part
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_')
        })
    {
        bail!("invalid target package name {package}");
    }
    Ok(())
}

fn validate_resource_identifier(resource_type: &str, name: &str) -> Result<()> {
    if resource_type.is_empty()
        || !resource_type
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'_')
    {
        bail!("resource type must use lowercase ASCII, digits, and underscores");
    }
    if name.is_empty()
        || !name
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'$' | b'.'))
    {
        bail!("resource name contains unsupported characters");
    }
    Ok(())
}

fn validate_relative_path(path: &Path) -> Result<()> {
    if path.as_os_str().is_empty() || path.is_absolute() {
        bail!("path must be non-empty and relative: {}", path.display());
    }
    for component in path.components() {
        match component {
            Component::Normal(value) if value != OsStr::new("") => {}
            _ => bail!("unsafe path: {}", path.display()),
        }
    }
    Ok(())
}

fn write_header(writer: &mut impl Write, header: &Header) -> Result<()> {
    let mut bytes = [0u8; HEADER_SIZE];
    bytes[0..8].copy_from_slice(MAGIC);
    bytes[8..10].copy_from_slice(&header.version.to_le_bytes());
    bytes[10..12].copy_from_slice(&(HEADER_SIZE as u16).to_le_bytes());
    bytes[12..16].copy_from_slice(&header.flags.to_le_bytes());
    bytes[16..24].copy_from_slice(&header.manifest_len.to_le_bytes());
    bytes[24..32].copy_from_slice(&header.payload_len.to_le_bytes());
    bytes[32..64].copy_from_slice(&header.manifest_sha256);
    bytes[64..96].copy_from_slice(&header.payload_sha256);
    writer.write_all(&bytes)?;
    Ok(())
}

fn read_header(reader: &mut (impl Read + Seek)) -> Result<Header> {
    let mut bytes = [0u8; HEADER_SIZE];
    reader.seek(SeekFrom::Start(0))?;
    reader.read_exact(&mut bytes)?;
    if &bytes[0..8] != MAGIC {
        bail!("invalid component magic");
    }
    let version = u16::from_le_bytes(bytes[8..10].try_into()?);
    let size = u16::from_le_bytes(bytes[10..12].try_into()?) as usize;
    if size != HEADER_SIZE {
        bail!("unexpected header size {size}");
    }
    if bytes[96..HEADER_SIZE].iter().any(|value| *value != 0) {
        bail!("reserved header bytes must be zero");
    }
    let flags = u32::from_le_bytes(bytes[12..16].try_into()?);
    let manifest_len = u64::from_le_bytes(bytes[16..24].try_into()?);
    let payload_len = u64::from_le_bytes(bytes[24..32].try_into()?);
    let mut manifest_sha256 = [0u8; 32];
    manifest_sha256.copy_from_slice(&bytes[32..64]);
    let mut payload_sha256 = [0u8; 32];
    payload_sha256.copy_from_slice(&bytes[64..96]);
    Ok(Header {
        version,
        flags,
        manifest_len,
        payload_len,
        manifest_sha256,
        payload_sha256,
    })
}

fn theme_fingerprint() -> Result<String> {
    let mut source = String::new();
    for setting in [
        ["get", "secure", "theme_customization_overlay_packages"],
        ["get", "secure", "ui_night_mode"],
        ["get", "system", "font_scale"],
    ] {
        let output = Command::new("settings").args(setting).output();
        match output {
            Ok(output) => {
                source.push_str(&String::from_utf8_lossy(&output.stdout));
                source.push('\n');
            }
            Err(error) => source.push_str(&format!("settings-error:{error}\n")),
        }
    }
    for color in [
        "system_primary_light",
        "system_primary_dark",
        "system_surface_light",
        "system_surface_dark",
        "system_on_surface_light",
        "system_on_surface_dark",
    ] {
        source.push_str(color);
        source.push('=');
        match lookup_android_color(color) {
            Ok(value) => source.push_str(&value),
            Err(error) => source.push_str(&format!("error:{error}")),
        }
        source.push('\n');
    }
    Ok(hex::encode(Sha256::digest(source.as_bytes())))
}

fn watch_theme(store: &Path, runtime_dir: &Path, interval_seconds: u64) -> Result<()> {
    ensure_root()?;
    if interval_seconds < 5 {
        bail!("watch interval must be at least 5 seconds");
    }
    fs::create_dir_all(runtime_dir)?;
    let fingerprint_path = runtime_dir.join("theme.fingerprint");
    loop {
        match theme_fingerprint() {
            Ok(current) => {
                let previous = fs::read_to_string(&fingerprint_path).unwrap_or_default();
                if previous.trim() != current {
                    if let Err(error) = apply_all(store) {
                        eprintln!("reapply after palette change failed: {error:#}");
                    }
                    let temporary = runtime_dir.join("theme.fingerprint.tmp");
                    fs::write(&temporary, current.as_bytes())?;
                    fs::rename(temporary, &fingerprint_path)?;
                }
            }
            Err(error) => eprintln!("theme fingerprint failed: {error:#}"),
        }
        thread::sleep(Duration::from_secs(interval_seconds));
    }
}

fn parse_u32(raw: &str) -> Result<u32> {
    let raw = raw.trim();
    if let Some(hex) = raw.strip_prefix("0x") {
        Ok(u32::from_str_radix(hex, 16)?)
    } else {
        Ok(raw.parse()?)
    }
}

fn package_installed(package: &str) -> bool {
    Command::new("pm")
        .args(["path", package])
        .output()
        .map(|output| output.status.success() && !output.stdout.is_empty())
        .unwrap_or(false)
}

fn ensure_root() -> Result<()> {
    let output = Command::new("id").arg("-u").output()?;
    if String::from_utf8_lossy(&output.stdout).trim() != "0" {
        bail!("this command requires root");
    }
    Ok(())
}

fn run_output<I, S>(command: &str, args: I) -> Result<Output>
where
    I: IntoIterator<Item = S>,
    S: AsRef<OsStr>,
{
    let output = Command::new(command).args(args).output()?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
        return Err(anyhow!(
            "{command} failed (status {}): {}{}{}",
            output.status,
            stderr,
            if !stderr.is_empty() && !stdout.is_empty() {
                " | "
            } else {
                ""
            },
            stdout
        ));
    }
    Ok(output)
}

fn run_cmd<I, S>(command: &str, args: I) -> Result<()>
where
    I: IntoIterator<Item = S>,
    S: AsRef<OsStr>,
{
    let _ = run_output(command, args)?;
    Ok(())
}

fn run_cmd_owned(command: &str, args: &[String]) -> Result<()> {
    run_cmd(command, args)
}

fn getprop_u32(name: &str) -> Option<u32> {
    let output = Command::new("getprop").arg(name).output().ok()?;
    String::from_utf8_lossy(&output.stdout).trim().parse().ok()
}

fn xml_escape(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&apos;")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn header_round_trip() {
        let header = Header {
            version: 1,
            flags: FLAG_ZSTD_TAR,
            manifest_len: 10,
            payload_len: 20,
            manifest_sha256: [1; 32],
            payload_sha256: [2; 32],
        };
        let mut data = Cursor::new(Vec::<u8>::new());
        write_header(&mut data, &header).unwrap();
        let decoded = read_header(&mut data).unwrap();
        assert_eq!(decoded.version, header.version);
        assert_eq!(decoded.flags, header.flags);
        assert_eq!(decoded.manifest_len, header.manifest_len);
        assert_eq!(decoded.payload_len, header.payload_len);
        assert_eq!(decoded.manifest_sha256, header.manifest_sha256);
        assert_eq!(decoded.payload_sha256, header.payload_sha256);
    }

    #[test]
    fn dimension_encoding_is_stable() {
        assert_eq!(encode_dimension("0dp").unwrap(), 1);
        assert_eq!(encode_dimension("16dp").unwrap(), 0x08000021);
        let value = encode_dimension("12.5sp").unwrap();
        assert_eq!(value & 0x0f, 2);
    }

    #[test]
    fn manifest_identifier_validation_allows_legacy_case() {
        validate_resource_identifier("color", "BW_100").unwrap();
        validate_resource_identifier("drawable", "bubble.right$night").unwrap();
    }
}
