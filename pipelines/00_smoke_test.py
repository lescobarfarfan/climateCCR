"""Phase-0 smoke test.

Exercises the whole ``infra`` layer end to end: load config, set the seed, log,
draw reproducible randomness, and write a run manifest. Run it after
``pip install -e .`` to confirm the package is wired correctly:

    python pipelines/00_smoke_test.py
"""

from __future__ import annotations

from climateCCR.infra import RunManifest, get_logger, load_config, set_seed


def main() -> None:
    config = load_config()  # configs/default.yaml
    config.paths.ensure()  # create results/, logs/, manifests/ if missing

    logger = get_logger("climateCCR.smoke", log_dir=config.paths.logs)
    logger.info("Project root: %s", config.paths.root)
    logger.info("Config: seed=%s n_paths=%s ccy=%s", config.seed, config.n_paths,
                config.settlement_currency)

    rng = set_seed(config.seed)
    draws = rng.standard_normal(3)
    logger.info("First three N(0,1) draws: %s", draws.tolist())

    manifest = RunManifest.create(seed=config.seed, config=config,
                                  project_root=config.paths.root)
    out_path = manifest.write(config.paths.manifests)
    logger.info("Wrote run manifest: %s", out_path)


if __name__ == "__main__":
    main()
