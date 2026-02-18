import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add project root to path for model imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models for autogenerate support
# flake8: noqa: F401
from app.models.geo import Base
from app.models.geo import (
    GeoLand, GeoBundesland, GeoRegierungsbezirk,
    GeoKreis, GeoOrt, GeoOrtsteil
)
from app.models.com import (
    ComUnternehmen, ComKontakt, ComOrganisation, ComUnternehmenOrganisation,
    ComUnternehmenIdentifikation, ComExternalId,
    ComMarke, ComSerie, ComLieferbeziehung, ComUnternehmenSortiment,
    ComDienstleistung, ComUnternehmenDienstleistung, ComBonitaet,
    ComUnternehmenBewertung, ComUnternehmenQuelldaten,
)
from app.models.partner import ApiPartner
from app.models.etl import (
    EtlSource, EtlTableMapping, EtlFieldMapping, EtlImportLog,
    EtlImportRecord, EtlImportFile, EtlMergeConfig, EtlMergeJoin,
)
from app.models.base import BasBewertungsplattform, BasColorPalette, BasSprache
from app.models.plugin import (
    PlgKategorie, PlgPlugin, PlgPluginVersion, PlgProjekttyp,
    PlgPreis, PlgProjekt, PlgLizenz, PlgLizenzHistorie
)
from app.models.branche import (  # noqa: F401
    BrnBranche, BrnVerzeichnis, BrnRegionaleGruppe,
    BrnGoogleKategorie, BrnGoogleMapping
)
from app.models.smart_filter import SmartFilter  # noqa: F401
from app.models.setting import SystemSetting  # noqa: F401
from app.models.recherche import (  # noqa: F401
    RecherchAuftrag, RecherchRohErgebnis,
)
from app.models.prod import (  # noqa: F401
    ProdWerteliste, ProdSortiment, ProdEigenschaft,
    ProdSortimentEigenschaft, ProdKategorie,
    ProdArtikel, ProdArtikelSortiment, ProdArtikelEigenschaft,
    ProdArtikelBild, ProdArtikelText,
)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
