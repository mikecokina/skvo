import gzip
import hashlib


def md5_raw_content(raw_content):
    md5 = hashlib.md5()
    md5.update(raw_content)
    md5_crc = md5.hexdigest()
    return md5_crc


def compress(content, level=7):
    return gzip.compress(content, level)


def decompress(content):
    return gzip.decompress(content)


def check_md5_crc(content, crc):
    return True if md5_raw_content(content) == crc else False


def sha512_content(content):
    sha512 = hashlib.sha512()
    sha512.update(content)
    sha512_hash = sha512.hexdigest()
    return sha512_hash


def sha256_content(content):
    sha256 = hashlib.sha256()
    sha256.update(content)
    sha256_hash = sha256.hexdigest()
    return sha256_hash


def normalize_ra(ra):
    sign = 1 if ra >= 0 else -1
    ra = (abs(ra) % 360) * sign
    return ra if ra >= 0 else ra + 360.0


"""
/* Create WHERE SIZE range */
$position_clause = array();

$size = array("ra" => false, "de" => false);
$size["de"] = array($ip["pos"]["de"] - $ip["size"]["de"], $ip["pos"]["de"] + $ip["size"]["de"]);

$size["ra"] = array(Fn::normalize_ra($ip["pos"]["ra"] - $ip["size"]["ra"]),
    Fn::normalize_ra($ip["pos"]["ra"] + $ip["size"]["ra"]));

if ($ip["size"]["ra"] >= 360 / 2.0) {
    $size["ra"] = array(0, 360);
}

if ($size["ra"][0] > $size["ra"][1]) {
    array_push($position_clause, "((Target.RA >= " . $size["ra"][0] . ") OR (Target.RA <= " . $size["ra"][1] . " AND Target.RA > 0))");
} else {
    array_push($position_clause, "(Target.RA >= " . $size["ra"][0] . " AND Target.RA <= " . $size["ra"][1] . ")");
}
array_push($position_clause, " AND (Target.DE >= " . $size["de"][0] . " AND Target.DE <= " . $size["de"][1] . ")");
"""


"""
    public static function calculateJD($isoDate)
    {
        $pattern = "/(\d{4})-(\d{2})-(\d{2})T(\d{2})\:(\d{2})\:(\d{2})/";

        preg_match($pattern, $isoDate, $match);
        $year = (int)$match[1];
        $month = (int)$match[2];
        $day = (int)$match[3];

        $hour = (int)$match[4];
        $min = (int)$match[5];
        $sec = (int)$match[6];
        $univTime = $hour + ($min / 60.0) + ($sec / 3600.0);

        $sign = ((100 * $year + $month - 190002.5) >= 0) ? 1 : -1;
        $part1 = 367 * $year;
        $part2 = floor((7 * ($year + floor(($month + 9) / 12.0))) / 4.0);
        $part3 = $day + floor((275.0 * $month) / 9.0);
        $part4 = 1721013.5 + ($univTime / 24.0);
        $part5 = 0.5 * $sign;
        $jd = $part1 - $part2 + $part3 + $part4 - $part5 + 0.5;
        return $jd;
    }
"""