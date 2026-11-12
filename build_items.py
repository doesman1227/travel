#!/usr/bin/env python3
"""場所の記録から items.json を書き出す。パーソナルデータベースの三大分類のひとつ。

行ったところ（ROWS）・また行きたいところ（PICKS）・行ってみたいところ（WANTS）の三レーン。
事実と評価を分けてあるのがこの形の肝で、行ったことは ROWS に一度だけ書き、
もう一度行きたい理由は PICKS に別で持つ。PICKS に載せた分だけ picks.html に出る。
「また行きたいところ」は一度行った上でのもう一度、「行ってみたいところ」はまだのところ。

旅についての考えそのものは note.html（旅のノート）にある。こちらは一覧の側。

★このファイルは公開リポジトリに入り、誰でも全文を読める。非公開という状態は
持たない方針なので、公開していいものだけを書く。住所や、どこに住んでいるかが
分かってしまう書き方はしない（「鳥の多い公園」のように、場所を特定しない呼び方にする）。
行った日も月までにして、日付までは書かない。

直し方は二通り。手元で直して python3 build_items.py を走らせるか、GitHub の編集画面で
このファイルだけを直してコミットするか。後者の場合は .github/workflows/build.yml が
代わりに走らせて items.json を作り直すので、手元のパソコンは要らない。どちらの場合も、
手元で続きを直すときは先に git pull しておく（向こうのコミットが増えているため）。
"""

import hashlib
import json
import re
from pathlib import Path

NOTE = ("場所・旅行（行ったところ・また行きたいところ・行ってみたいところ）。"
        "build_items.py が書き出す。直すのはあちら。")

# 行ったところ。区切りは | で、順番は
# slug | 題名 | 年 | 一行 | リンク | 元になった記録
# 年は行った年。分からないものは空にしておく（「時期不明」に入る）。
ROWS = """
mountain-climb|週末の登山|2026|||../musings/posts/p143.html
park|鳥の多い公園||||
gym-bath|ジムの大きなお風呂||||
cinema|映画館||||
konpira|金毘羅宮||||
karasawa|涸沢カール||||
kamikochi|上高地||||
fukashima|深島||||
letao|ルタオ本店||||
oze|尾瀬ヶ原||||
imai-sakura|今井の桜||||
yamanohana|尾瀬 山の鼻小屋||||
bana|馬菜 銀座本店||||
imakin|お食事処 いまきん食堂||||
kabeyu|壁湯温泉 共同浴場||||
yufugawa|由布川峡谷||||
tomonaga|友永パン屋||||
suisaitei|水哉亭||||
himebotaru|ヒメボタルの見られる場所||||
daikanbo|大観峰||||
bogatsuru|坊ガツル||||
futagami|二上神社||||
tenan|そば処 天庵||||
hatozu|波当津海水浴場||||
shioyu|塩湯||||
matama|真玉海岸||||
mamedake|豆岳珈琲||||
gyosantei|魚山亭||||
ebisumaru|市場食堂 ゑびす丸||||
teshima|豊島美術館||||
okunoin|高野山 奥之院||||
british-villa|英国大使館別荘記念公園||||
nantai|日本料理 なんたい||||
zenjiro|たんや善治郎 仙台駅牛たん通り店||||
mikoda|盛岡神子田朝市||||
yukyu|悠久||||
shichibei|観音食堂 丼屋 七兵衛||||
shichifuku|七福温泉 宇戸の庄||閉業||
"""

# また行きたいところ。ここに載せた分だけ picks.html に出る。
# 文は self.json と前の items.json にあったものをそのまま移した。
PICKS = {
    "mountain-climb": "頂上に着いたとき、下山したあと、眠る前。大変だったからこそ、"
                      "そのあとの喜びが大きかった。登山の翌日、仕事が苦にならず頭がすっきりしていた。",
    "park": "家からすぐ行ける。いまの家を気に入っている理由のひとつ。",
    "gym-bath": "運動のあとにほどける。人のいる場所にいることも目的のうち。",
    "cinema": "週末に行く。日常から離れて作品に入る時間。",
    # ここから下は Google マップの「また行きたい場所」リストから移した。
    # 理由はまだ書いていないので、ひとまず場所の種類を入れてある。
    "konpira": "神社",
    "karasawa": "景勝地",
    "kamikochi": "景勝地",
    "fukashima": "島",
    "letao": "洋菓子店",
    "oze": "自然保護公園",
    "imai-sakura": "観光名所",
    "yamanohana": "山小屋",
    "bana": "レストラン",
    "imakin": "和食店",
    "kabeyu": "日帰り温泉",
    "yufugawa": "景勝地",
    "tomonaga": "ベーカリー",
    "suisaitei": "魚料理店",
    "himebotaru": "ヒメボタル",
    "daikanbo": "山頂",
    "bogatsuru": "観光名所",
    "futagami": "神社",
    "tenan": "蕎麦店",
    "hatozu": "浜",
    "shioyu": "海鮮料理店",
    "matama": "景勝地",
    "mamedake": "カフェ・喫茶",
    "gyosantei": "海鮮料理店",
    "ebisumaru": "海鮮料理店",
    "teshima": "美術館",
    "okunoin": "仏教寺院",
    "british-villa": "記念公園",
    "nantai": "純和食店",
    "zenjiro": "牛タン店",
    "mikoda": "マーケット",
    "yukyu": "寿司店",
    "shichibei": "海鮮丼専門店",
}

# 行ってみたいところ。区切りは | で、順番は
# slug | 題名 | 一行 | メモ | 領域 | 細目 | 状態 | リンク | 元になった記録
# 領域は下の USES の領域名から選ぶ（違う語はビルドで止まる）。細目は自由語でよい。
# 状態に「いま」と書くと、want.html の先頭の節に入る。空なら「これから」。
WANTS = """
tsukuba|筑波山||自然の雄大さに、心から感動できる場所へ。|自然|山|||
overseas|海外の、心を動かされる場所||普段とはまったく違う景色に触れ、感動する体験をしたい。|遠くの国|海外|||
small-trip|行ったことのない街へ、小旅行||週末に別の場所に泊まる。いつもの散歩道を一本変えるくらいの小さな非日常から。|街と建築|小旅行|||../musings/posts/p072.html
historic-town|歴史ある街を歩き、建築や美術に出会う||古い建物や絵画を前に、それを作った人たちの思いや工夫に思いを馳せたい。|街と建築|歴史ある街|||../way-of-life/#pillars
mile-trip|マイルで飛行機に乗る旅||普段の支出から貯めたマイルで、飛行機に乗ってどこかへ。|遠くの国|飛行機|||../musings/posts/p057.html
"""

# 領域と細目。字下げの無い行が領域で 領域名|英字|アイコン|参照先、
# 字下げした行が細目で 細目名|slug,slug。同じものは一つの細目にだけ置く。
# 細目が一行も無い領域は、まだ行ったところが無いもの。
# 「近所と日常」は旅のノートの「非日常の段階」の一段目にあたる受け皿で、
# いつもの散歩道や週末に行く場所を置く。
USES = """
近所と日常|NEARBY|pin|note.html#steps
  公園|park
  おふろ|gym-bath
  映画館|cinema
自然|NATURE|tree|note.html#touch
  景勝地|kamikochi,yufugawa,daikanbo
  湿原|oze
  島と海|fukashima,hatozu,matama
  桜とホタル|imai-sakura,himebotaru
街と建築|TOWN|home|note.html#touch
  寺社|konpira,futagami,okunoin
  建築と公園|british-villa
  市場|mikoda
美術と展示|ART|frame|note.html#touch
  美術館|teshima
温泉と宿|ONSEN|bath|
  温泉|kabeyu,shichifuku
  山小屋|yamanohana
キャンプと山|CAMP|tent|note.html#steps
  登山|mountain-climb
  山|karasawa,bogatsuru
食べもの|FOOD|meal|
  和食|bana,imakin,tenan,nantai,zenjiro
  海鮮|suisaitei,shioyu,gyosantei,ebisumaru,yukyu,shichibei
  パンと菓子と喫茶|letao,tomonaga,mamedake
遠くの国|ABROAD|globe|note.html#support
"""

# 領域に入れないもの。いまは無い。
OUT = """
"""

# 領域に出していないものについての一行。出していないものが無ければ空。
LEFT = ""

ASSETS = ["style.css", "app.js"]
PAGES = ["index.html", "picks.html", "want.html"]
SLUG = re.compile(r"^[a-z0-9-]+$")
YEAR = re.compile(r"^[12][0-9]{3}$")
# app.js が領域の外のものと「いま」の節に使うアイコン。どのページにも要る。
ALWAYS = ["star", "sparkle"]


def rows(block, cols):
    """| 区切りの表を読む。列の数が合わない行はその場で止める。"""
    out = []
    for n, line in enumerate(block.strip().splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != len(cols):
            raise SystemExit(f"{n}行目の列が{len(parts)}個（{len(cols)}個のはず）: {line}")
        out.append(dict(zip(cols, parts)))
    return out


def check_common(it, where):
    """slug・年・リンクの書き方を確かめる。どれも直せば通る形の間違い。"""
    if not SLUG.match(it["slug"]):
        raise SystemExit(f"{where} の slug は英小文字・数字・ハイフンだけ: {it['slug']}")
    if it.get("year") and not YEAR.match(it["year"]):
        raise SystemExit(f"{where} の年は4桁: {it['slug']} の {it['year']}")
    if it.get("url") and not it["url"].startswith(("http://", "https://")):
        raise SystemExit(f"{where} のリンクは http/https だけ: {it['slug']}")
    if it.get("source") and not it["source"].startswith(("./", "../")):
        raise SystemExit(f"{where} の元になった記録は相対パスで: {it['slug']} の {it['source']}")


def check_icons(here, names):
    """使うアイコンが三枚ぜんぶに埋まっているか確かめる。

    優待で一度やられている。want.html にアイコンを三つしか持たせないまま銘柄を足して、
    カードの丸が空のまま公開された。線画は各HTMLに埋め込む作りなので、
    一枚だけ足し忘れても他の二枚では正しく出てしまい、見落としやすい。
    """
    for page in PAGES:
        have = set(re.findall(r'<symbol id="ic-([a-z0-9-]+)"', (here / page).read_text(encoding="utf-8")))
        missing = sorted(set(names) - have)
        if missing:
            raise SystemExit(f"{page} にアイコンが埋まっていない: {missing}")


def stamp_assets(here):
    """style.css と app.js の URL に中身のハッシュを付ける。

    一度来た人のブラウザには前の app.js が残っている。ページとデータだけ新しくなると
    古いコードが新しい形の items.json を読むことになり、節がまるごと出なくなる。
    中身が変わればURLも変わるようにして、取り違えが起きないようにする。
    """
    tag = hashlib.sha256(b"".join((here / f).read_bytes() for f in ASSETS)).hexdigest()[:8]
    touched = []
    for page in here.glob("*.html"):
        t = u = page.read_text(encoding="utf-8")
        for f in ASSETS:
            u = re.sub(rf'({re.escape(f)})(\?v=[0-9a-f]+)?"', rf'\1?v={tag}"', u)
        if u != t:
            page.write_text(u, encoding="utf-8")
            touched.append(page.name)
    return f"共通ファイルの版を {tag} にした" + (f"（{'・'.join(touched)}）" if touched else "（変更なし）")


def main():
    items = rows(ROWS, ["slug", "title", "year", "note", "url", "source"])
    wants = rows(WANTS, ["slug", "title", "note", "memo", "use", "sub", "state", "url", "source"])

    for it in items:
        check_common(it, "ROWS")
    for w in wants:
        check_common(w, "WANTS")

    slugs = [i["slug"] for i in items] + [w["slug"] for w in wants]
    dup = sorted({s for s in slugs if slugs.count(s) > 1})
    if dup:
        raise SystemExit(f"slug が重なっている: {dup}")

    by_slug = {i["slug"]: i for i in items}
    unknown = sorted(set(PICKS) - set(by_slug))
    if unknown:
        raise SystemExit(f"PICKS に ROWS に無い slug がある: {unknown}")
    for slug, memo in PICKS.items():
        by_slug[slug]["memo"] = memo

    # 領域と細目。字下げの無い行が領域、字下げした行が細目。
    uses, seen = [], []
    for line in USES.strip().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  "):
            if not uses:
                raise SystemExit(f"領域より先に細目が来ている: {line.strip()}")
            sub, codes = line.strip().split("|")
            codes = [c.strip() for c in codes.split(",") if c.strip()]
            uses[-1]["subs"].append(sub)
            uses[-1]["n"] += len(codes)
            seen += codes
            for c in codes:
                if c in by_slug:
                    by_slug[c]["use"], by_slug[c]["sub"] = uses[-1]["name"], sub
        else:
            name, en, ic, ref = line.split("|")
            uses.append({"name": name, "en": en, "icon": ic, "ref": ref, "subs": [], "n": 0})

    dup = sorted({c for c in seen if seen.count(c) > 1})
    if dup:
        raise SystemExit(f"USES で二つの細目に置かれた slug がある: {dup}")

    ghost = sorted(c for c in seen if c not in by_slug)
    if ghost:
        raise SystemExit(f"USES に ROWS に無い slug がある: {ghost}")

    out_slugs = [c.strip() for c in OUT.replace("\n", "").split(",") if c.strip()]
    stray = sorted(c for c in out_slugs if c not in by_slug)
    if stray:
        raise SystemExit(f"OUT に ROWS に無い slug がある: {stray}")

    # 行を足したときの入れ忘れを防ぐ。どこかの領域に置くか、出さないと決めるか。
    nowhere = sorted(c for c in by_slug if c not in seen and c not in out_slugs)
    if nowhere:
        raise SystemExit(f"USES にも OUT にも無い slug がある: {nowhere}")

    names = {u["name"] for u in uses}
    bad = sorted({w["use"] for w in wants if w["use"] and w["use"] not in names})
    if bad:
        raise SystemExit(f"WANTS の領域が領域名に無い: {bad}")
    bad = sorted({w["state"] for w in wants if w["state"] not in ("", "いま")})
    if bad:
        raise SystemExit(f"WANTS の状態は空か「いま」だけ: {bad}")

    here = Path(__file__).resolve().parent
    check_icons(here, [u["icon"] for u in uses] + ALWAYS)

    # 写真は images/<slug>.jpg に置いてあれば拾う。items.json は生成物なので、
    # 写真があるかどうかはファイルの側で決める（誰も items.json に書き戻さない）。
    for it in items + wants:
        if (here / "images" / (it["slug"] + ".jpg")).exists():
            it["img"] = f"images/{it['slug']}.jpg"

    data = {
        "note": NOTE,
        "items": [{k: v for k, v in i.items() if v} for i in items],
        "wants": [{k: v for k, v in w.items() if v} for w in wants],
        "uses": uses,
        "left": LEFT,
    }
    (here / "items.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"items.json を書いた（{len(items)}件・お気に入り{len(PICKS)}件・これから{len(wants)}件）")
    print(stamp_assets(here))


if __name__ == "__main__":
    main()
