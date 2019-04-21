import logging
import re
from typing import List, Optional, Tuple
from cmp_version import cmp_version, cmp

logger = logging.getLogger(__name__)


def number_of_unique_values(values: List[str]) -> int:
    """
    Count number of unique strings in list, ignoring the case
    """
    return len(set(map(lambda s: s.lower(), values)))


class Release:
    VALID_TYPES = ["stable", "beta", "alpha", "rc", "unstable"]
    type = None
    date = None
    __str__ = None

    def __init__(self, string=None):
        self.__str__ = string

    @property
    def string(self):
        return self.__str__

    @string.setter
    def string(self, string):
        self.__str__ = string

    def __cmp__(self, other):
        if self.date is None or other.date is None:
            return cmp_version(self.__init__, other.__init__)
        else:
            return cmp(self.date, other.date)

    def __lt__(self, other):
        return bool(self.__cmp__(other) < 0)

    def __le__(self, other):
        return bool(self.__cmp__(other) <= 0)

    def __gt__(self, other):
        return bool(self.__cmp__(other) > 0)

    def __ge__(self, other):
        return bool(self.__cmp__(other) >= 0)

    def __eq__(self, other):
        # Todo: handle subtypes (beta is unstable…)
        return bool(self.__cmp__(other) == 0 and self.type == other.type)

    def __ne__(self, other):
        # Todo: handle subtypes (beta is unstable…)
        return bool(self.__cmp__(other) != 0 or self.type != other.type)

    def __repr__(self):
        return "Release(%s, date=%s, type=%s)" % (self.__str__, self.date, self.type)

    def is_stable(self):
        return bool(self.type == "stable")


def extract_version(string: str, name: Optional[str] = None) -> Optional[Release]:
    """
    Heuristic to extract a version-number from a string.

    See test file for supported formats. Returns None if no unambiguously
    version number could be found.

    :param string: the string to search
    :param name: the name of the program
    :return: None or a tuple of two strings:
             - type of version ("stable", "beta", "alpha", "rc" or "unstable")
             - version number
    """
    string = string.strip()
    version = Release()

    # Remove a prefix of the name of the program if existent
    if name:
        namere = re.compile(r"^" + re.escape(name) + r"[ _/-]?", re.IGNORECASE)
        string = re.sub(namere, "", string)

    # Remove common prefixes/postfixes
    string = re.sub(
        r"^(releases|release|rel|version|vers|v\.)[ _/-]?",
        "",
        string,
        flags=re.IGNORECASE,
    )
    string = re.sub(r"^(v|r)(?<![0-9])", "", string, flags=re.IGNORECASE)
    string = re.sub(
        r"(^|[._ -])(final|release)([._ -]|$)", " ", string, flags=re.IGNORECASE
    )

    # Replace underscore/hyphen with dots if only underscores/hyphens are used
    if re.fullmatch(r"[0-9_]*", string):
        string = string.replace("_", ".")
    if re.fullmatch(r"[0-9-]*", string):
        string = string.replace("-", ".")

    # Detect type of version
    words = ["stable", "beta", "alpha", "rc", "pre", "preview", "b\d", "dev"]
    res = re.findall(r"(" + "|".join(words) + r")", string, re.IGNORECASE)
    if number_of_unique_values(res) == 1:
        version.type = res[0].lower()
        if version.type[0] == "b":
            version.type = "beta"
        if version.type not in version.VALID_TYPES:
            version.type = "unstable"
    elif number_of_unique_values(res) > 1:
        return None

    # Detect version string
    gen = re.compile(
        r"((?<=\s)|^)(\d{1,3}(\.\d{1,3})+[a-z]?([._ -]?(alpha|beta|pre|rc|b|stable|preview|dev)[._-]?\d*|-\d+)?)(\s|$)",
        re.IGNORECASE,
    )
    res = gen.findall(string)
    # remove "stable" from version string
    res = list(map(lambda s: re.sub(r"[._-]stable[._-]?", "", s[1]), res))
    if number_of_unique_values(res) == 1:
        version.string = res[0]
    else:
        # If the string contains nothing but a version-number we are more gratefully with what we accept
        full = re.compile(r"[1-9]\d{0,4}", re.IGNORECASE)
        if full.fullmatch(string):
            version.string = string

    if version.string is not None:
        # if we don't find any indication about the state of the version,
        # we assume it's a stable version
        if version.type is None:
            version.type = "stable"
        return version

    return None
