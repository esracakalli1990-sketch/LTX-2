# LTX-2 Türkçe Kılavuz

Bu kılavuz, LTX-2 deposunun ne olduğunu, ne işe yaradığını ve nasıl kullanıldığını Türkçe olarak adım adım anlatır. Ayrıntılı ve güncel bilgi için her bölümde ilgili İngilizce belgeye bağlantı verilmiştir.

---

## 1. LTX-2 nedir?

**LTX-2**, [Lightricks](https://ltx.io) tarafından geliştirilen, **ses ve videoyu birlikte üreten** açık erişimli bir yapay zekâ temel modelidir (foundation model). DiT (Diffusion Transformer) mimarisine dayanır ve tek bir modelde şunları sunar:

- **Senkronize ses + video üretimi**: Konuşma, efekt sesleri ve görüntü aynı anda, birbiriyle uyumlu üretilir.
- **Yüksek kalite**: 4K'ya (3840×2176) kadar çözünürlük.
- **Farklı hız/kalite modları**: Hızlı "distilled" moddan, yavaş ama prodüksiyon kalitesindeki DFR moduna kadar.
- **Açık ağırlıklar**: Model dosyaları Hugging Face üzerinden indirilebilir.

Teknik olarak model, 14 milyar parametreli bir video akışı ve 5 milyar parametreli bir ses akışından oluşan, iki akış arasında çift yönlü dikkat (cross-attention) kullanan asimetrik bir transformer'dır. Güncel önerilen sürüm **LTX-2.5** (22B), metin kodlayıcı olarak LTX için ince ayar yapılmış **Gemma 4 12B** kullanır. Eski sürüm **LTX-2.3** de desteklenir (Gemma 3 kullanır).

Faydalı bağlantılar:
- Web sitesi: <https://ltx.io>
- Model: <https://huggingface.co/Lightricks/LTX-2.5>
- Tarayıcıda deneme: <https://console.ltx.video/playground>
- Makale: <https://arxiv.org/abs/2601.03233>
- Discord: <https://discord.gg/ltxplatform>

---

## 2. Ne işe yarar? (Kullanım senaryoları)

| Görev | Açıklama | Kullanılacak pipeline |
|---|---|---|
| Metinden video (T2V) | Yazdığınız açıklamadan sesli video üretir | `DistilledPipeline`, `DFRPipeline` |
| Görselden video (I2V) | Bir fotoğrafı canlandırır | `DistilledPipeline`, `DFRPipeline`, `TI2VidTwoStagesPipeline` |
| Anahtar kare (keyframe) ara doldurma | Birden çok görsel arasında geçiş videosu üretir | `TI2VidTwoStagesPipeline` |
| Sesten video (A2V) | Bir ses dosyasına uygun video üretir | `A2VidPipelineTwoStage` |
| Videodan videoya (V2V) | Mevcut videoyu IC-LoRA ile dönüştürür (stil, kontrol vb.) | `ICLoraPipeline` |
| Retake | Mevcut videonun belirli bir zaman aralığını yeniden üretir | `RetakePipeline` |
| Dublaj (Dub-It) | Konuşmayı, konuşmacının sesini ve dudak hareketlerini koruyarak yeniden ifade eder | `DubItPipeline` |
| SDR → HDR | Normal videoyu HDR'a çevirir (BT.2020/HLG + EXR çıktısı) | `HDRICLoraPipeline` |
| Metinden ses (T2A) | Sadece ses üretir (video yok) | `T2AOneStagePipeline` |
| Kendi modelinizi eğitme | LoRA, IC-LoRA veya tam ince ayar (fine-tuning) | `ltx-trainer` paketi |

---

## 3. Depo yapısı

Depo bir **monorepo**'dur; `packages/` altında birbirine bağlı paketler bulunur:

```
LTX-2/
├── README.md                 # Ana İngilizce belge
├── MODELS-LTX-2.3.md         # Eski LTX-2.3 model dosyaları listesi
├── CHANGELOG.md              # Sürüm notları
├── LICENSE, LICENSE-2, LICENSE-2_x   # Lisanslar
├── pyproject.toml            # uv çalışma alanı (workspace) tanımı
├── .claude/skills/train-model/       # Yapay zekâ ajanı ile eğitim için hazır "skill"
└── packages/
    ├── ltx-core/             # Çekirdek: model tanımları, bileşenler, yükleyiciler
    ├── ltx-pipelines/        # Hazır üretim (inference) pipeline'ları ve CLI
    ├── ltx-trainer/          # Eğitim / ince ayar araçları
    └── ltx-kernels/          # Özel CUDA/C++ çekirdekleri (FP8, NVFP4, çoklu GPU vb.)
```

### 3.1 `ltx-core` — Çekirdek kütüphane
Modelin "ham" hâli. Diğer paketler bunu kullanır.
- `model/`: Transformer, Video VAE, Audio VAE, Vocoder (mel spektrogramdan dalga formu), Upscaler
- `components/`: Scheduler'lar (gürültü takvimi), Guider'lar (CFG, STG, APG), Noiser'lar, Patchifier'lar
- `conditioning/`: Görsel, video, anahtar kare koşullandırması
- `loader/`: `.safetensors` yükleme, LoRA birleştirme, bellek yönetimi
- `quantization/`: FP8, blok bazlı FP8/FP6, NVFP4
- `block_streaming/`: Transformer bloklarını GPU'ya tek tek aktararak düşük bellekle çalıştırma
- `text_encoders/gemma`: Gemma metin kodlayıcı

Ayrıntı: [packages/ltx-core/README.md](packages/ltx-core/README.md)

### 3.2 `ltx-pipelines` — Kullanıma hazır pipeline'lar
Model yükleme, kodlama, gürültü giderme, çözme ve dosyaya yazma işlerinin hepsini yapar. **Her pipeline komut satırından çalıştırılabilir** (`python -m ltx_pipelines.<modül>`).

Ayrıntı: [packages/ltx-pipelines/README.md](packages/ltx-pipelines/README.md)

### 3.3 `ltx-trainer` — Eğitim araçları
Kendi verinizle LoRA, IC-LoRA veya tam ince ayar yapmanızı sağlar. Veri hazırlama betikleri (sahne bölme, otomatik altyazı/caption üretme, ön işleme) ve hazır YAML konfigürasyonları içerir.

Ayrıntı: [packages/ltx-trainer/README.md](packages/ltx-trainer/README.md)

### 3.4 `ltx-kernels` — Performans çekirdekleri
İsteğe bağlı, derlenmiş CUDA çekirdekleri: çoklu GPU iletişimi, blok bazlı FP8 GEMM, Blackwell GPU'lar için NVFP4 ve diffusion VAE için hızlandırılmış komşuluk dikkati (neighborhood attention).

Ayrıntı: [packages/ltx-kernels/README.md](packages/ltx-kernels/README.md)

---

## 4. Gereksinimler

- **İşletim sistemi**: Linux önerilir (eğitim için Linux + CUDA zorunlu; `triton` sadece Linux'ta çalışır).
- **GPU**: NVIDIA CUDA GPU. 22B model büyük olduğundan bol VRAM gerekir.
  - Üretim (inference): Yetersiz bellekte FP8 kuantizasyon ve offload ile çalıştırılabilir (bkz. Bölüm 7).
  - Eğitim: Standart konfigürasyon için **80 GB+ VRAM**; 32 GB'lık kartlar (ör. RTX 5090) için `t2v_lora_low_vram.yaml`.
- **Disk**: LTX-2.5 hızlı başlangıç dosyaları yaklaşık **66 GiB**.
- **Yazılım**: Python, [uv](https://docs.astral.sh/uv/getting-started/installation/) paket yöneticisi, Hugging Face hesabı.

---

## 5. Kurulum

### 5.1 Depoyu klonlayın
```bash
git clone https://github.com/Lightricks/LTX-2.git
cd LTX-2
```

### 5.2 Bağımlılıkları kurun
```bash
uv sync --extra natten
```
`natten` eki, diffusion video VAE için en hızlı arka uçtur ve sadece Linux + CUDA'da kurulur. Windows/macOS'ta otomatik atlanır; kod Triton ya da standart (eager) uygulamaya geri döner, yani aynı komut her yerde çalışır.

Alternatif: `uv sync --frozen` veya tek paket için `pip install -e packages/ltx-pipelines`.

### 5.3 Model dosyalarını indirin
Önce Hugging Face'e giriş yapın ve model sayfasında lisans koşullarını kabul edin:
```bash
hf auth login
hf download Lightricks/LTX-2.5 \
    diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors \
    text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors \
    vae/ltx-2.5-video-vae-bf16.safetensors \
    vae/ltx-2.5-audio-vae-bf16.safetensors \
    latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors \
    --local-dir models/ltx-2.5
```
> **401/403 hatası alırsanız**: Model sayfasında koşulları kabul ettiğinizden ve **Read** yetkili bir token kullandığınızdan emin olun (fine-grained token'larda "read gated repos" izni açık olmalı).

### 5.4 Model dosyaları ne işe yarar?

| Dosya | Görevi | Zorunlu mu? |
|---|---|---|
| `...-distilled-transformer` | Hızlı (az adımlı) ana model. Distilled, DFR, IC-LoRA, Dub-It kullanır | Seçeneklerden biri |
| `...-dev-transformer` | Tam model. Rehberli iki aşamalı pipeline'lar (TI2Vid, Keyframe, A2Vid) kullanır | Seçeneklerden biri |
| `gemma4-12b-with-proj-ltx-2.5` | Metin kodlayıcı (Google'ın standart Gemma 4'ü yerine geçmez!) | Her zaman |
| `ltx-2.5-video-vae` | Video kodlayıcı/çözücü (diffusion decoder, yüksek kalite) | Biri gerekli |
| `ltx-2.5-video-vae-conv` | Daha hafif konvolüsyonel çözücü | Biri gerekli |
| `ltx-2.5-audio-vae` | Ses kodlayıcı/çözücü | Ses üreten pipeline'larda |
| `spatial-upscaler-x2` | Gizli uzayda (latent) 2x büyütme | İki aşamalı pipeline'larda |
| `temporal-upscaler-x2` | Kare hızını artırma | DFR'de `--temporal-upscalings` ile |
| `distilled-lora-450` | Tam modelle çalışan iki aşamalı pipeline'larda 2. aşama | TI2Vid / Keyframe / A2Vid |
| `ic-lora-pixel-spatial-upscaler` | DFR'nin detaylandırma LoRA'sı (ayrı repoda) | DFR |
| `duration-head` | `--num-frames` vermeden video uzunluğunu prompttan tahmin eder | İsteğe bağlı |

Tam liste ve indirme bağlantıları: [README.md → Full Model List](README.md#full-model-list). Eski sürüm için: [MODELS-LTX-2.3.md](MODELS-LTX-2.3.md). **Not**: LTX-2.3 ve LTX-2.5 dosyaları birbirinin yerine kullanılamaz; bir LoRA sadece eğitildiği modelle çalışır.

---

## 6. Kullanım: Video üretmek

### 6.1 İlk videonuz (DistilledPipeline — en hızlı)
```bash
uv run python -m ltx_pipelines.distilled \
    --transformer-path       models/ltx-2.5/diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors \
    --text-encoder-path      models/ltx-2.5/text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors \
    --video-vae-path         models/ltx-2.5/vae/ltx-2.5-video-vae-bf16.safetensors \
    --audio-vae-path         models/ltx-2.5/vae/ltx-2.5-audio-vae-bf16.safetensors \
    --spatial-upsampler-path models/ltx-2.5/latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors \
    --num-frames 121 \
    --seed 42 \
    --output-path output.mp4 \
    --prompt "A golden retriever runs across a sunny meadow toward the camera, ears flapping, as birds chirp in the background. The camera tracks low to the ground with shallow depth of field, warm afternoon light."
```
- `--num-frames 121`: 24 fps'de yaklaşık 5 saniye. Kare sayıları `8k+1` biçiminde olmalı (ör. 97, 121).
- `--seed`: Aynı seed ile aynı sonucu tekrar elde edersiniz.
- Çıktı `output.mp4` dosyasına **sesiyle birlikte** yazılır.

### 6.2 Prodüksiyon kalitesi (DFR)
DFR (Diffusion Fidelity Rendering), **aynı distilled transformer**'ı kullanır; ek olarak üretilmiş ara anahtar kareler ve bir detaylandırma geçişi yapar. Daha yavaştır ve daha çok VRAM ister. Tam (dev) transformer'ı **vermeyin**.

Önce detaylandırma LoRA'sını indirin:
```bash
hf download Lightricks/LTX-2.5-22b-IC-LoRA-Pixel-Spatial-Upscaler \
    ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors \
    --local-dir models/ltx-2.5/loras
```
Sonra:
```bash
uv run python -m ltx_pipelines.dfr_pipeline \
    --transformer-path       models/ltx-2.5/diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors \
    --text-encoder-path      models/ltx-2.5/text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors \
    --video-vae-path         models/ltx-2.5/vae/ltx-2.5-video-vae-bf16.safetensors \
    --audio-vae-path         models/ltx-2.5/vae/ltx-2.5-audio-vae-bf16.safetensors \
    --detailing-lora         models/ltx-2.5/loras/ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors \
    --spatial-upsampler-path models/ltx-2.5/latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors \
    --num-frames 121 --seed 42 \
    --output-path output_dfr.mp4 \
    --prompt "..."
```
- Varsayılan çözünürlük 1024×1536, 24 fps.
- 4K için: `--width 3840 --height 2176` (2160 değil!).
- Kare hızını 2x/4x artırmak için `--temporal-upscalings 1` veya `2` (temporal upscaler gerekir).

Ayrıntı: [Running DFR](packages/ltx-pipelines/docs/pipelines.md#running-dfr)

### 6.3 Görselden video (Image-to-Video)
Görsel koşullandırma `--image` bayrağıyla verilir:
```
--image <DOSYA> <KARE_İNDEKSİ> <GÜÇ> [replace|guide]
```
Örnek: ilk kareyi bir fotoğrafa sabitlemek için
```bash
--image foto.png 0 1.0
```
- `replace`: Kareyi doğrudan görselle değiştirir; sadece `0` veya `1 + 8k` (1, 9, 17, ...) karelerinde kullanılabilir.
- `guide`: Videoyu herhangi bir karede görsele doğru yönlendirir (anahtar kare ara doldurma için idealdir).

Python API'de karşılığı:
```python
from ltx_pipelines.utils.types import ImageConditioningInput

opening = ImageConditioningInput.replace("opening.png", frame_idx=0, strength=1.0)
guide   = ImageConditioningInput.guide("guide.png", frame_idx=80, strength=0.8)
```
Ayrıntı: [Conditioning Types](packages/ltx-pipelines/docs/conditioning.md)

### 6.4 Hangi pipeline'ı seçmeliyim?
```
Mevcut bir videoyu düzenleyecek misiniz?      → RetakePipeline
Videoyu bir ses dosyası mı yönlendirecek?     → A2VidPipelineTwoStage
HDR / EXR gerekiyor mu?                       → --hdr bayrağı veya HDRICLoraPipeline
Referans videodan dönüşüm (V2V)?              → ICLoraPipeline
Birden çok anahtar kare arası geçiş?          → TI2VidTwoStagesPipeline (--image ... guide)
Sadece metin/tek görsel:
   ├─ En hızlı                                → DistilledPipeline
   ├─ En yüksek kalite / yüksek fps           → DFRPipeline
   └─ CFG/STG rehberli iki aşama              → TI2VidTwoStagesPipeline
```
`TI2VidOneStagePipeline` daha çok öğrenme/prototip amaçlıdır. Tam karşılaştırma tablosu: [Pipeline Selection Guide](packages/ltx-pipelines/docs/pipeline-selection.md).

Bir pipeline'ın tüm seçeneklerini görmek için:
```bash
uv run python -m ltx_pipelines.distilled --help
```

---

## 7. Sık kullanılan CLI bayrakları

| Bayrak | Anlamı |
|---|---|
| `--prompt "..."` | Üretilecek sahnenin açıklaması |
| `--seed <sayı>` | Tekrarlanabilirlik için rastgelelik tohumu (varsayılan 10) |
| `--num-frames <sayı>` | Kare sayısı (`8k+1`) |
| `--width`, `--height` | Çözünürlük |
| `--output-path` | Çıktı dosyası |
| `--quantization fp8-cast` | bf16 ağırlıkları anında FP8'e çevirir → daha az VRAM |
| `--quantization fp8-scaled-mm` | FP8 checkpoint + Hopper (H100) ve üstü GPU'lar için |
| `--offload cpu` / `disk` | Transformer ağırlıklarını RAM'de / diskte tutar → GPU belleği azalır (daha yavaş) |
| `--lora <yol> [güç]` | LoRA uygular (birden çok kez kullanılabilir) |
| `--enhance-prompt` | Promptu yerleşik iyileştirici ile zenginleştirir |
| `--compile` | `torch.compile` ile hızlandırma |
| `--hdr {SRGB_LINEAR,ACESCG,ACESCCT}` | EXR girişlerinin renk uzayı; HDR çıktı üretir |
| `--chunk-pixel-frames`, `--chunk-carry-frames` | Uzun videoları pencereler hâlinde üretir |

**GPU belleğiniz yetmiyorsa** ilk deneyeceğiniz şey:
```bash
--quantization fp8-cast --offload cpu
```
Tüm bayraklar: [installation.md → Common CLI flags](packages/ltx-pipelines/docs/installation.md#common-cli-flags)

---

## 8. Performans ipuçları

- **Hız için DistilledPipeline** kullanın (1. aşama 8 adım, 2. aşama 4 adım).
- **FP8 kuantizasyon** ile bellek kullanımını düşürün.
- **Dikkat (attention) hızlandırmaları**: Hopper GPU'larda FlashAttention 3, veri merkezi Blackwell'de (B200) FlashAttention 4 (`uv pip install 'flash-attn-4==4.0.0b9'`). Diğer GPU'larda otomatik olarak PyTorch SDPA kullanılır.
- **Gradient estimation** ile adım sayısını 40'tan 20–30'a indirebilirsiniz.
- Yeterli VRAM'iniz varsa aşamalar arası bellek temizliğini kapatabilirsiniz.
- **Çoklu GPU**: Tek makinede birden fazla GPU ile tek bir üretimin **süresini** kısaltır; büyük modeli sığdırmak için değildir (her GPU'da tam kopya bulunur). Bkz. [Multi-GPU Inference](packages/ltx-pipelines/docs/multigpu/README.md).

Ayrıntı: [Optimization Tips](packages/ltx-pipelines/docs/optimization.md)

---

## 9. İyi prompt yazma

Prompt'u **İngilizce**, tek bir akıcı paragraf hâlinde, bir görüntü yönetmeninin çekim listesi gibi yazın. **200 kelimeyi geçmeyin.** Önerilen yapı:

1. Ana eylemi tek cümleyle başlatın.
2. Hareket ve jestleri ayrıntılandırın.
3. Karakter/nesne görünümlerini net tanımlayın.
4. Arka plan ve ortamı anlatın.
5. Kamera açısını ve hareketini belirtin.
6. Işık ve renkleri tarif edin.
7. Ani değişiklikleri/olayları not edin.
8. **Ses**: Model ses de ürettiği için konuşmaları tırnak içinde, sesin tonunu ve ortam seslerini yazın (ör. *"he speaks with a deep voice, saying, 'Hello.'"*).

Ek rehber: <https://ltx.io/blog/prompting-guide-for-ltx-2>

---

## 10. Kendi modelinizi eğitmek (`ltx-trainer`)

### 10.1 Desteklenen eğitim modları
Metinden video, görselden video, video uzatma, IC-LoRA (video/ses/ses+video), sesten video, videodan ses (foley), video inpainting/outpainting, metinden ses, ses uzatma, ses inpainting ve tam ince ayar. Her biri için `packages/ltx-trainer/configs/` altında hazır YAML var (ör. `t2v_lora.yaml`, `i2v_lora.yaml`, `v2v_ic_lora.yaml`).

### 10.2 Adım adım ilk eğitim
```bash
uv sync
cd packages/ltx-trainer

# 1) Uzun videoları sahnelere bölün (isteğe bağlı)
uv run python scripts/split_scenes.py input.mp4 sahneler/ --filter-shorter-than 5s

# 2) Videolara otomatik açıklama (caption) üretin (isteğe bağlı)
uv run python scripts/caption_videos.py sahneler/ --output dataset.json

# 3) Ön işleme: latent ve metin gömmelerini hesaplayın (.precomputed/ klasörüne yazar)
uv run python scripts/process_dataset.py dataset.json \
    --resolution-buckets "960x544x49" \
    --model-path /yol/ltx-checkpoint.safetensors \
    --text-encoder-path /yol/gemma
```

### 10.3 Konfigürasyon
`configs/t2v_lora.yaml` dosyasını kopyalayıp yolları düzenleyin. LTX-2.5'in parçalı (split) dosyaları için:
```yaml
model:
  model_path: "/yol/diffusion_models/ltx-2.5-22b-dev-transformer-bf16.safetensors"
  text_encoder_path: "/yol/text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors"
  video_vae_path: "/yol/vae/ltx-2.5-video-vae-bf16.safetensors"
  audio_vae_path: "/yol/vae/ltx-2.5-audio-vae-bf16.safetensors"

data:
  preprocessed_data_root: "/yol/.precomputed"

output_dir: "outputs/ilk_egitimim"
```

### 10.4 Eğitimi başlatın
```bash
uv run python scripts/train.py configs/t2v_lora.yaml
# Çoklu GPU:
uv run accelerate launch scripts/train.py configs/t2v_lora.yaml
```

Eğittiğiniz LoRA'yı üretimde `--lora <yol> <güç>` ile kullanırsınız.

> **İpucu**: Claude Code gibi bir ajan ortamı kullanıyorsanız depodaki [`train-model`](.claude/skills/train-model/SKILL.md) skill'i; donanımınızı ve verinizi inceleyip doğru modu seçer, veriyi hazırlar, eğitimi başlatır ve izler.

> **Önemli**: Ön işlenmiş metin özellikleri model + Gemma çiftine özgüdür. LTX-2.3'ten 2.5'e geçerken yeni bir klasöre ön işleme yapın veya `--overwrite` kullanın.

Ayrıntılı belgeler: [Quick Start](packages/ltx-trainer/docs/quick-start.md) · [Dataset Preparation](packages/ltx-trainer/docs/dataset-preparation.md) · [Training Modes](packages/ltx-trainer/docs/training-modes.md) · [Configuration Reference](packages/ltx-trainer/docs/configuration-reference.md) · [Troubleshooting](packages/ltx-trainer/docs/troubleshooting.md)

---

## 11. Diğer entegrasyonlar

- **ComfyUI**: Görsel düğüm tabanlı arayüzde kullanmak için <https://github.com/Lightricks/ComfyUI-LTXVideo/>
- **Filigran (watermark)**: `--marker-root-path` ile isteğe bağlı VideoSeal/AudioSeal işaretleme. Bkz. [marking.md](packages/ltx-pipelines/docs/marking.md)
- **HDR / EXR**: Bkz. [hdr.md](packages/ltx-pipelines/docs/hdr.md)

---

## 12. Sık karşılaşılan sorunlar

| Sorun | Çözüm |
|---|---|
| İndirmede 401/403 | Hugging Face'te model koşullarını kabul edin, Read token ile `hf auth login` yapın |
| CUDA out of memory | `--quantization fp8-cast --offload cpu` (daha da az bellek için `--offload disk`), çözünürlüğü / kare sayısını düşürün, konvolüsyonel video VAE'yi deneyin |
| Metin kodlayıcı sürüm hatası | Google'ın standart Gemma'sını değil, depodaki LTX'e özel Gemma dosyasını kullanın |
| LoRA etkisiz/hatalı | LoRA'nın kullandığınız model sürümüyle (2.3 / 2.5) eğitildiğinden emin olun |
| 4K'da boyut hatası | Yükseklik 2160 değil **2176** olmalı |
| Kare sayısı uyarısı | `--num-frames` değerini `8k+1` yapın (97, 121, ...) |

---

## 13. Lisans

Model ve kod **LTX Community License** kapsamındadır:
- LTX-2.5 ve sonrası: [LICENSE-2_x](LICENSE-2_x) (11 Ağustos 2026)
- LTX-2 / LTX-2.3: [LICENSE-2](LICENSE-2) (5 Ocak 2026)

Ticari kullanım dâhil haklarınız ve kısıtlamalarınız için lisans metnini mutlaka okuyun. Bu kılavuz hukuki tavsiye değildir.

---

*Bu kılavuz, depodaki İngilizce belgeler temel alınarak hazırlanmıştır. Bayraklar ve dosya adları zamanla değişebilir; şüphe durumunda `--help` çıktısına ve orijinal belgelere başvurun.*
