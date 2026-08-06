# Release signing

Do not commit a keystore or its passwords.

The tag workflow expects these encrypted repository secrets:

- `MONET_KEYSTORE_B64`
- `MONET_KEYSTORE_PASSWORD`
- `MONET_KEY_ALIAS`
- `MONET_KEY_PASSWORD`

Use one stable project release key for every release. Rotating the key can cause Android to reject an existing overlay package as a signature mismatch.
