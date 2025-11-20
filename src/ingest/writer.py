import psycopg2
from psycopg2 import errors
from typing import List

from core.config import Config
from ingest.providers.base import TradeRecord
from ingest.writer_errors import WriterError

def write(records: List[TradeRecord]) -> int:
    if not records:
        return 0

    # Cache symbol -> symbol_id lookups to avoid repeated SELECTs
    symbol_cache = {}
    cnt_written = 0

    try:
        with psycopg2.connect(Config.DB_URL) as conn:
            cur = conn.cursor()

            for record in records:
                cur.execute("INSERT INTO raw_trades (symbol, ts, price, size, source) VALUES (%s, %s, %s, %s, %s)",
                            (record.symbol, record.ts, record.price, record.size, record.source))
                cnt_written += 1

            # Leaving the with-block commits the transaction automatically

        return cnt_written

    except errors.UniqueViolation as e:
        raise WriterError("Database unique constraint violation: {}".format(e)) from e

    except errors.ForeignKeyViolation as e:
        raise WriterError("Foreign key violation: {}".format(e)) from e

    except errors.InvalidDatetimeFormat as e:
        raise WriterError("Invalid timestamp format in database write: {}".format(e)) from e

    except psycopg2.OperationalError as e:
        raise WriterError("Database connection or operational error: {}".format(e)) from e

    except psycopg2.Error as e:
        raise WriterError("General database error during write: {}".format(e)) from e

    except Exception as e:
        raise WriterError("Unexpected error during write: {}".format(e)) from e
