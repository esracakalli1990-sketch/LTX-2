# Hattuşa — Hitit Başkentinin Hikâyesi (≈18 saniyelik sinematik video planı)

Bu dosya, LTX-2 ile üretilecek videonun sahne planını ve hazır İngilizce prompt'ları içerir.

## Yapı

LTX-2 tek seferde birkaç saniyelik klip üretir. Video, 4 sahneden (her biri ~5 sn, 121 kare @ 24 fps) oluşur ve sahneler aralarında yumuşak geçişlerle birleştirilir (toplam ≈17,6 sn).

| # | Sahne | Süre | Geçiş (sonraki sahneye) |
|---|---|---|---|
| 1 | Şafakta Hattuşa — havadan şehir ve surlar | 5 sn | Yumuşak çözülme (fade) |
| 2 | Aslanlı Kapı — Hitit savaş arabaları şehre giriyor | 5 sn | Karartma (fade to black) |
| 3 | Tapınakta kâtip — çivi yazılı tablet (Kadeş Antlaşması) | 5 sn | Kayarak geçiş (slide) |
| 4 | Yazılıkaya'nın tanrı kabartmaları → bugünkü harabeler | 5 sn | Son |

Önerilen ayarlar: yatay 16:9, 24 fps, `--num-frames 121`, kalite için DFR (API'de en yüksek kalite seçeneği), sahneler arasında aynı `seed`.

> Ekranda yazı istemiyoruz: model metin yazmakta zayıftır. Başlık ("HATTUŞA · M.Ö. 1650–1180") sonradan eklenir.

---

## Sahne 1 — Şafakta Hattuşa

```
A sweeping aerial drone shot glides at dawn over the ancient Hittite capital of Hattusa on the rocky highlands of central Anatolia, around 1300 BC. Massive cyclopean stone walls with rectangular towers snake along steep ridges, enclosing flat-roofed mud-brick houses, narrow streets, and a vast temple complex below. Thin columns of smoke rise from cooking fires, and tiny figures in long woolen robes move between the buildings. The camera slowly descends and pushes forward toward the great southern rampart as the first golden sunlight breaks over the distant mountains, casting long shadows across the dry grass and limestone outcrops. Soft morning mist hangs in the valleys. The color palette is warm amber, ochre, and pale blue. The sound is a gentle highland wind, distant birdsong, and a single low, resonant bronze horn echoing across the valley, followed by a slow, deep cinematic drum beat.
```

## Sahne 2 — Aslanlı Kapı ve savaş arabaları

```
A low-angle tracking shot moves toward the Lion Gate of Hattusa, a towering stone gateway flanked by two massive carved lions emerging from the huge granite blocks, their mouths open and manes detailed. Three Hittite war chariots, each drawn by two dark horses and carrying three warriors in conical bronze helmets, leather armor, and long braided hair, thunder through the gate in a cloud of golden dust. Spears and round shields catch the bright late-morning sunlight. Guards with bronze axes stand on the walls above. The camera stays low near the ground as the chariot wheels pass close to the lens, then tilts up to reveal the carved lions against a clear sky. Strong sunlight, deep shadows, warm earthy tones. The sound is pounding horse hooves, the rattling and creaking of wooden chariot wheels on stone, warriors shouting a short command, and an epic orchestral drum swell.
```

## Sahne 3 — Kâtip ve çivi yazılı tablet

```
A slow cinematic push-in inside a dim stone chamber of the Great Temple of Hattusa, lit only by flickering oil lamps and a shaft of dusty sunlight from a high window. An elderly Hittite scribe with a gray beard, wearing a long dark-red woolen robe and a simple cap, sits at a low wooden table and carefully presses a reed stylus into a wet clay tablet, forming rows of small wedge-shaped cuneiform marks. Shelves behind him are stacked with hundreds of clay tablets. The camera moves into an extreme close-up of the tablet as fresh wedges appear in the soft clay, with shallow depth of field and the lamp flame glowing softly in the background. Warm golden and deep brown tones, rich contrast. The sound is the quiet scratching of the stylus in clay, the soft crackle of lamp flames, distant temple chanting, and a low, mysterious string melody.
```

## Sahne 4 — Yazılıkaya'dan bugüne

```
A slow lateral dolly shot moves along the rock walls of the Yazilikaya open-air sanctuary near Hattusa at night, where a procession of twelve identical Hittite gods carved in relief marches in a line, each wearing a tall pointed conical hat, short tunic, and curved shoes, carrying sickle-shaped swords. Warm torchlight sweeps across the ancient carvings, making the figures seem to move in the flickering glow. The camera continues moving, and the scene gradually transforms as night turns into a golden sunset over the present-day ruins of Hattusa: weathered stone foundations, the restored section of the mud-brick city wall, and the Lion Gate standing alone in the tall golden grass. The camera rises slowly into a wide final shot of the empty highland under a vast orange and purple sky. The sound is crackling torches, a deep slow drum, a soft wordless choir rising, and finally the gentle evening wind.
```

---

## Sahneleri birleştirme (ffmpeg)

Klipler `s1.mp4 … s4.mp4` olarak kaydedildikten sonra:

```bash
ffmpeg -i s1.mp4 -i s2.mp4 -i s3.mp4 -i s4.mp4 -filter_complex "\
[0:v][1:v]xfade=transition=fade:duration=0.8:offset=4.2[v1];\
[v1][2:v]xfade=transition=fadeblack:duration=0.8:offset=8.4[v2];\
[v2][3:v]xfade=transition=smoothleft:duration=0.8:offset=12.6[v3];\
[v3]drawtext=text='HATTUŞA':fontsize=96:fontcolor=white:x=(w-tw)/2:y=(h-th)/2-40:enable='between(t,0.8,3.6)':alpha='if(lt(t,1.6),t-0.8,if(gt(t,2.8),3.6-t,1))',\
drawtext=text='M.Ö. 1650 – 1180':fontsize=44:fontcolor=white:x=(w-tw)/2:y=(h-th)/2+60:enable='between(t,0.8,3.6)':alpha='if(lt(t,1.6),t-0.8,if(gt(t,2.8),3.6-t,1))'[v];\
[0:a][1:a]acrossfade=d=0.8[a1];[a1][2:a]acrossfade=d=0.8[a2];[a2][3:a]acrossfade=d=0.8[a]" \
-map "[v]" -map "[a]" -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k hattusa.mp4
```

Offset değerleri her klibin 5,0 sn olduğu varsayımıyla hesaplanmıştır (`offset = önceki toplam − 0,8`). Klip süreleri farklı çıkarsa `ffprobe` ile ölçülüp güncellenir.

## İsteğe bağlı: Türkçe anlatım metni (~17 sn)

> "Anadolu'nun kalbinde, üç bin yıldan uzun süre önce... Hititlerin başkenti Hattuşa yükseldi. Aslanlı Kapı'dan savaş arabaları geçti; kâtipler tarihin bilinen en eski barış antlaşmalarından birini kile kazıdı. Bugün taşlar hâlâ konuşuyor."

Anlatım ayrı bir seslendirme aracıyla üretilip videonun ses kanalına alçak sesle karıştırılabilir.

## Tarihî notlar

- Hattuşa (bugün Çorum, Boğazkale), yaklaşık M.Ö. 1650–1180 arasında Hitit başkentiydi; UNESCO Dünya Mirası listesindedir.
- Aslanlı Kapı, Kral Kapı ve Sfenksli Kapı şehrin anıtsal kapılarıdır.
- Kadeş Antlaşması (M.Ö. ~1259): III. Hattuşili ile Mısır firavunu II. Ramses arasında; Hitit nüshası Hattuşa'da kil tablet olarak bulunmuştur.
- Yazılıkaya, 12 tanrı alayı kabartmasıyla bilinen açık hava tapınağıdır.
- Hitit savaş arabaları üç kişilik mürettebatıyla tanınırdı.
