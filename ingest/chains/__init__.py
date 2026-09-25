"""Thin JSON-RPC clients and decoders for the two chains. No third-party chain SDKs:
the surface we need (getLogs, getTransaction, a little ABI) is small enough to own,
which keeps the dependency tree auditable."""
