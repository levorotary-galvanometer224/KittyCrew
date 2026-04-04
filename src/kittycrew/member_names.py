from __future__ import annotations

import random
import re
from collections.abc import Iterable
from pathlib import Path

CANDIDATE_MEMBER_NAMES: list[str] = [
    "Mochi Whiskers",
    "Poppy Paws",
    "Luna Biscuit",
    "Milo Mittens",
    "Clover Tail",
    "Pepper Purr",
    "Nori Buttons",
    "Olive Tuft",
    "Maple Socks",
    "Sunny Pebble",
    "Coco Nibbles",
    "Pumpkin Bloom",
    "Hazel Puff",
    "Teddy Marmalade",
    "Pippa Velvet",
    "Basil Toes",
    "Waffle Nose",
    "Daisy Curls",
    "Benny Whisk",
    "Rosie Pounce",
    "Toffee Paws",
    "Juniper Bean",
    "Archie Fluff",
    "Mabel Mews",
    "Otis Dandelion",
    "Ivy Snuggle",
    "Mango Tumble",
    "Ruby Sprout",
    "Finn Clover",
    "Maisie Purr",
    "Biscuit Hop",
    "Nala Trinket",
    "Toby Patches",
    "Willow Pebbles",
    "Freya Nuzzle",
    "Theo Buttercup",
    "Penny Winks",
    "Remy Fuzz",
    "Millie Buttons",
    "Leo Tinsel",
    "Zoe Marzipan",
    "Alfie Twirl",
    "Bonnie Whimsy",
    "Jasper Mallow",
    "Honey Sable",
    "Louie Pip",
    "Piper Trinket",
    "Chester Purrkins",
    "Elsie Tofu",
    "Murphy Velvet",
    "Skye Pudding",
    "Gus Acorn",
    "Tilly Crumbs",
    "Hugo Bramble",
    "Suki Petal",
    "Walter Waffles",
    "Dolly Fable",
    "Rory Pebble",
    "Phoebe Tinsel",
    "Benny Marshmallow",
    "Minnie Thimble",
    "Ollie Pompom",
    "Sadie Plume",
    "Harvey Button",
    "Pru Feather",
    "Rufus Noodle",
    "Nina Pickles",
    "Cosmo Pawsley",
    "Bea Tumble",
    "Ginger Dot",
    "Percy Muffin",
    "Winnie Purrl",
    "Felix Wisp",
    "Dotty Maple",
    "Cleo Snickers",
    "Bruno Pecan",
    "Birdie Bubbles",
    "Ralph Custard",
    "Indie Fawn",
    "Mimi Pockets",
    "Bodhi Tater",
    "Cali Twinkle",
    "Ozzy Buttons",
    "Nellie Moss",
    "Kiki Sherbet",
    "Maxie Purrcy",
    "Dottie Tofu",
    "Sage Pollen",
    "Rocco Biscotti",
    "Lottie Pawsworth",
    "Yuki Crumpet",
    "Trixie Meringue",
    "Juno Whispurr",
    "Bambi Chestnut",
    "Frankie Popcorn",
    "Marnie Nuzzles",
    "Ziggy Paws",
    "Evie Butterbean",
    "Koda Whiskers",
    "Pixie Tart",
]


def normalize_member_name(name: str) -> str:
    return " ".join(name.split()).strip()


def normalize_member_name_key(name: str) -> str:
    return normalize_member_name(name).casefold()


def build_member_workdir(project_root: Path, member_title: str) -> Path:
    normalized = normalize_member_name(member_title)
    slug = re.sub(r"[\\/]+", "-", normalized)
    slug = re.sub(r"\s+", "-", slug)
    slug = slug.strip(" .") or "member"
    return (Path("/tmp/KittyCrew") / slug)


def pick_available_member_name(used_names: Iterable[str]) -> str | None:
    used_keys = {normalize_member_name_key(name) for name in used_names}
    available = [name for name in CANDIDATE_MEMBER_NAMES if normalize_member_name_key(name) not in used_keys]
    if not available:
        return None
    return random.choice(available)
