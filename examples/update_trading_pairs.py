from argparse import ArgumentParser

import fp_core as fnc
import task_io as tio
import utils
import shared_logic as shared


# ---------------------------------------------------------------


def http_trading_pairs_task():
    url = 'https://api.exchange.coinbase.com/products'
    return tio.http_task("GET", url, {"Accept": "application/json"}) \



def get_trading_pairs_json_data_task():
    return shared.reliable_http_task(http_trading_pairs_task()) \
        .map(tio.http_response_data)  \
        .chain(tio.to_json_task_fn)


# -------------------------------------------------------


def upsert_trading_pairs(trading_pairs_json: dict) -> fnc.TaskFunc:
    """
    :: json -> (connection -> Task(string))
    """
    def _upsert_pairs(connection):
        cur = connection.cursor()
        # TODO try: cur = connection.cursor(prepared = True)

        # trading_pairs_json = list(trading_pairs_json1)[:50]

        rows_upserted = 0
        item_count = len(trading_pairs_json)
        for item in trading_pairs_json:
            cur.execute(
                "INSERT INTO trading_pairs (id, quote_currency, post_only, limit_only, cancel_only, trading_disabled)  \
                    VALUES (?, ?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE   \
                        post_only=?, limit_only=?, cancel_only=?, trading_disabled=?", (
                    item["id"],
                    item["quote_currency"], item["post_only"], item["limit_only"], item["cancel_only"], item["cancel_only"],
                    item["post_only"], item["limit_only"], item["cancel_only"], item["trading_disabled"]
                )
            )
            rows_upserted += cur.rowcount

        connection.commit()
        return f"Upserted: [{rows_upserted}] out of [{item_count}]"

    return tio.checked_sync_task_fn("upsert trading pairs to DB", _upsert_pairs)


# ===============================================================

parser = ArgumentParser()
parser.add_argument("--dbconfig", type=str,
                    help="input DB config JSON file name", default='dbconf.json')

args = parser.parse_args()


get_trading_pairs_json_data_task()  \
    .chain(lambda trading_pairs_json: shared.on_db_task(
        args.dbconfig,
        lambda conn: upsert_trading_pairs(trading_pairs_json)(conn)
    )
).fork(utils.print_and_exit_error(1), print)
