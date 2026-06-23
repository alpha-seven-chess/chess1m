#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chess960 and Chess1M Starting Position Generator
=================================================
Generates all 921,600 unique starting positions formed by independently
assigning any Chess960 back-rank to White (rank 1) and Black (rank 8),
then labels each position with helper flags. All positions are expressed
as FEN strings.

Chess1M is a superset of Chess960 in which White's and Black's back ranks
are chosen independently from the 960 valid Chess960 back-rank arrangements
(Scharnagl IDs 0–959), yielding 960 × 960 = 921,600 distinct starting
positions. The 960 positions where both sides share the same back rank are
exactly the standard Chess960 positions.

All FEN strings are intended for use with chess960=True in any consuming
engine or library, so that castling rights are interpreted correctly
regardless of king and rook file placement.

Outputs
-------
chess960_sp_idn_fen_ref.csv
    960 rows — one per Chess960 starting position.
    Columns: chess960_scharnagl_sp_idn, rank_1_white, rank_8_black,
             standard_fen, shredder_fen, is_chess960, is_classical.

chess1m_sp_idn_fen_ref.csv
    921,600 rows — one per Chess1M starting position.
    Columns: chess1m_sp_idn, chess960_scharnagl_sp_idn_white,
             chess960_scharnagl_sp_idn_black, rank_1_white, rank_8_black,
             standard_fen, shredder_fen, is_chess960, is_classical.

Dependencies
------------
python-chess >= 1.11.2  (pip install chess)
pandas       >= 3.0.2

Usage
-----
    python chess960_chess1m_reference_positions.py [--output-dir PATH]

    --output-dir  Directory where CSV files are written.
                  Defaults to the script's own directory.

Author  : alpha-seven-chess
Created : 2026-06-20
"""

import argparse
import itertools
import logging
from pathlib import Path

import chess
import pandas as pd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_ranks(fen: str) -> pd.Series:
    """Return rank_1_white and rank_8_black extracted from a FEN string.

    Parameters
    ----------
    fen : str
        A valid FEN string.

    Returns
    -------
    pd.Series
        Series with keys ``rank_1_white`` (White's back rank, uppercase)
        and ``rank_8_black`` (Black's back rank, lowercase).
    """
    ranks = fen.split()[0].split("/")
    return pd.Series({"rank_1_white": ranks[7], "rank_8_black": ranks[0]})


def create_starting_fen(rank_1_white: str, rank_8_black: str) -> str:
    """Build a Shredder-FEN string from White and Black back ranks.

    Passes ``KQkq`` to ``chess.Board`` with ``chess960=True``, which
    automatically converts castling rights to unambiguous Shredder notation
    (e.g. ``HAha``) based on the actual king and rook positions in the
    given back ranks.

    Parameters
    ----------
    rank_1_white : str
        White's back rank, e.g. ``'RNBQKBNR'``.
    rank_8_black : str
        Black's back rank, e.g. ``'rnbqkbnr'``.

    Returns
    -------
    str
        Shredder-FEN string for the starting position with correct
        castling rights.
    """
    fen = f"{rank_8_black}/pppppppp/8/8/8/8/PPPPPPPP/{rank_1_white} w KQkq - 0 1"
    return chess.Board(fen, chess960=True).fen(shredder=True)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build_chess960_reference() -> pd.DataFrame:
    """Generate the 960-row Chess960 reference table.

    Returns
    -------
    pd.DataFrame
        Columns: chess960_scharnagl_sp_idn, rank_1_white, rank_8_black,
        standard_fen, shredder_fen, is_chess960, is_classical.
    """
    logging.info("Building Chess960 reference table (960 positions)...")

    df = pd.DataFrame(
        {"standard_fen": [chess.Board.from_chess960_pos(i).fen() for i in range(960)]}
    )
    df["chess960_scharnagl_sp_idn"] = range(960)
    df[["rank_1_white", "rank_8_black"]] = df["standard_fen"].apply(extract_ranks)
    df["shredder_fen"] = df.apply(
        lambda row: create_starting_fen(row["rank_1_white"], row["rank_8_black"]), axis=1
    )
    df["is_chess960"] = 1
    df["is_classical"] = (df["standard_fen"] == chess.STARTING_FEN).astype(int)

    df = df[[
        "chess960_scharnagl_sp_idn", "rank_1_white", "rank_8_black",
        "standard_fen", "shredder_fen", "is_chess960", "is_classical",
    ]]

    logging.info("Chess960 reference table built. Shape: %s", df.shape)
    return df


def build_chess1m_reference(df_960: pd.DataFrame) -> pd.DataFrame:
    """Generate the 921,600-row Chess1M reference table.

    Castling strings for each side are precomputed from ``df_960`` and
    joined by Scharnagl ID, avoiding 921,600 ``chess.Board`` instantiations.

    Parameters
    ----------
    df_960 : pd.DataFrame
        Output of :func:`build_chess960_reference`.

    Returns
    -------
    pd.DataFrame
        Columns: chess1m_sp_idn, chess960_scharnagl_sp_idn_white,
        chess960_scharnagl_sp_idn_black, rank_1_white, rank_8_black,
        standard_fen, shredder_fen, is_chess960, is_classical.
    """
    logging.info("Building Chess1M reference table (921,600 positions)...")

    # All White x Black Scharnagl ID combinations
    df = pd.DataFrame(
        itertools.product(range(960), repeat=2),
        columns=["chess960_scharnagl_sp_idn_white", "chess960_scharnagl_sp_idn_black"],
    )
    df["chess1m_sp_idn"] = range(len(df))

    # Precompute per-side castling strings from the Chess960 reference table.
    # White castling letters are uppercase (e.g. 'HF'), Black are lowercase (e.g. 'hf').
    # Concatenating them gives the full Shredder castling field for any combination.
    white_lookup = df_960[["chess960_scharnagl_sp_idn", "rank_1_white", "shredder_fen"]].copy()
    white_lookup["castling_white"] = (
        white_lookup["shredder_fen"].apply(lambda f: f.split()[2]).str.extract(r'([A-H]+)')
    )

    black_lookup = df_960[["chess960_scharnagl_sp_idn", "rank_8_black", "shredder_fen"]].copy()
    black_lookup["castling_black"] = (
        black_lookup["shredder_fen"].apply(lambda f: f.split()[2]).str.extract(r'([a-h]+)')
    )

    # Join back-rank and castling strings for each side
    df = (
        df
        .merge(
            white_lookup[["chess960_scharnagl_sp_idn", "rank_1_white", "castling_white"]],
            left_on="chess960_scharnagl_sp_idn_white",
            right_on="chess960_scharnagl_sp_idn",
            how="left",
        )
        .drop(columns="chess960_scharnagl_sp_idn")
        .merge(
            black_lookup[["chess960_scharnagl_sp_idn", "rank_8_black", "castling_black"]],
            left_on="chess960_scharnagl_sp_idn_black",
            right_on="chess960_scharnagl_sp_idn",
            how="left",
        )
        .drop(columns="chess960_scharnagl_sp_idn")
    )

    # Combine per-side castling letters into the full Shredder castling field
    shredder_castling = (
        df["castling_white"].fillna("") + df["castling_black"].fillna("")
    ).replace("", "-")

    # Build FEN strings
    fen_body = df["rank_8_black"] + "/pppppppp/8/8/8/8/PPPPPPPP/" + df["rank_1_white"]
    df["shredder_fen"] = fen_body + " w " + shredder_castling + " - 0 1"
    df["standard_fen"] = fen_body + " w KQkq - 0 1"

    df = df.drop(columns=["castling_white", "castling_black"])

    # Flags
    df["is_chess960"] = (
        df["rank_1_white"].str.lower() == df["rank_8_black"].str.lower()
    ).astype(int)
    df["is_classical"] = (df["standard_fen"] == chess.STARTING_FEN).astype(int)

    df = df[[
        "chess1m_sp_idn", "chess960_scharnagl_sp_idn_white", "chess960_scharnagl_sp_idn_black",
        "rank_1_white", "rank_8_black", "standard_fen", "shredder_fen",
        "is_chess960", "is_classical",
    ]]

    logging.info(
        "Chess1M reference table built. Shape: %s | Chess960 positions: %d | Classical: %d",
        df.shape, df["is_chess960"].sum(), df["is_classical"].sum(),
    )
    return df


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Chess960 and Chess1M starting position reference CSVs."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent,
        help="Directory where output CSV files are written (default: script directory).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df_960 = build_chess960_reference()
    df_960.to_csv(args.output_dir / "chess960_sp_idn_fen_ref.csv", index=False)
    logging.info("Saved chess960_sp_idn_fen_ref.csv")

    df_1m = build_chess1m_reference(df_960)
    df_1m.to_csv(args.output_dir / "chess1m_sp_idn_fen_ref.csv", index=False)
    logging.info("Saved chess1m_sp_idn_fen_ref.csv")

    logging.info("Done.")
