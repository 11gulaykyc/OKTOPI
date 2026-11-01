# İçerik Ekleme Kılavuzu

Konu anlatımları, sorular ve etkileşimli grafikler koddan bağımsız olarak `content/` altındaki JSON dosyalarında tutulur.
Kod değiştirmeden içerik eklenebilir. Her dosya `content/schemas/` altındaki Pydantic şemalarıyla doğrulanır.

```text
content/
├── curriculum/
│   ├── grade-9/index.json          # tema → konu → alt konu ağacı ve kazanımlar
│   ├── grade-9/topics/<konu>.json  # konu anlatımı (+ etkileşimli grafikler)
│   └── oyss/oyss.json              # OYSS bilgilendirme ve takvim
└── questions/grade-9/<konu>.json   # kavram yanılgısı etiketli sorular
```

## Altın kurallar

1. Her değişiklikten sonra doğrulamayı çalıştırın. Hata varsa komut dosya ve alan yolunu yazarak durur:
   ```powershell
   cd backend
   .\.venv\Scripts\python manage.py validate_content
   ```
2. Var olan bir dosyayı değiştirdiğinizde `version` değerini artırın (`1.0` → `1.1`).
3. Kimlik kalıpları sabittir:

   | Öğe | Kalıp | Örnek |
   | --- | --- | --- |
   | Tema | `th-<sınıf>-<sıra>` | `th-9-4` |
   | Konu / alt konu | `top-<sınıf>-<ad>[-<alt>]` | `top-9-tri`, `top-9-tri-angles` |
   | Soru | `q-<sınıf>-<konu>-<3 hane>` | `q-9-tri-001` |
   | Kazanım | `MAT.<sınıf>.<tema>.<no>` | `MAT.9.4.1` |
   | Kavram yanılgısı | `MISC_<KONU>_<AÇIKLAMA>` | `MISC_TRI_ANGLE_SUM_360` |
   | Grafik | `viz-<sınıf>-<ad>` | `viz-9-tri-angles` |

4. Metinlerde LaTeX `$...$` (satır içi) ve `$$...$$` (blok) ile yazılır. Ayrıca `**kalın**`, `*italik*`, `- ` ile madde ve `1. ` ile numaralı liste desteklenir. JSON içinde ters bölü çift yazılır: `"$\\frac{1}{8}$"`.
5. Anlatım dili akran dilidir: samimi ve kısa cümleler, günlük hayattan örnekler.
6. İçerik ilk istekte belleğe alınır. Değişikliği görmek için backend sürecini yeniden başlatın.

## 1. Yeni konu anlatımı

1. `curriculum/grade-X/index.json` içinde konunun ve alt konularının tanımlı olduğundan emin olun.
2. `curriculum/grade-X/topics/<konu-id>.json` dosyasını oluşturun:

```json
{
  "id": "top-9-func",
  "version": "1.0",
  "grade": 9,
  "theme_id": "th-9-2",
  "title": "Fonksiyon Kavramı ve Doğrusal Fonksiyonlar",
  "summary": "Bir iki cümlelik özet.",
  "estimated_minutes": 35,
  "learning_objectives": ["Öğrencinin kazanacağı beceri…"],
  "sections": [
    {
      "id": "top-9-func-slope",
      "title": "Eğim",
      "body": "Markdown + LaTeX anlatım…",
      "formulas": [{ "label": "İki noktadan eğim", "latex": "m = \\frac{y_2 - y_1}{x_2 - x_1}" }],
      "examples": [{ "title": "…", "problem": "…", "steps": ["…"], "answer": "…" }],
      "tip": "İpucu (isteğe bağlı)",
      "common_mistakes": ["Sık yapılan hata…"]
    }
  ],
  "reinforcement_question_ids": ["q-9-func-001"],
  "visualizations": []
}
```

3. `index.json` içinde konunun `content_file` alanını `"topics/<konu-id>.json"` yapın.

Doğrulamada denetlenenler:
- `id`, `grade` ve `theme_id` müfredat ağacıyla aynı olmalıdır.
- Her bölümün `id` değeri o konunun bir **alt konusu** olmalıdır. Kavram yanılgısı yönlendirmeleri öğrenciyi bu bölümlere götürür.
- `reinforcement_question_ids` içindeki sorular soru havuzunda bulunmalıdır.

## 2. Yeni soru

`questions/grade-X/<konu-id>.json` dosyası (dosya adı = `topic_id`, klasör = `grade-X`):

```json
{
  "version": "1.0",
  "grade": 9,
  "topic_id": "top-9-exp",
  "questions": [
    {
      "id": "q-9-exp-001",
      "version": "1.0",
      "grade": 9,
      "topic_id": "top-9-exp",
      "topic": "Üslü İfadeler ve Denklemler",
      "subtopic_id": "top-9-exp-neg",
      "subtopic": "Negatif Kuvvet",
      "learning_outcome": "MAT.9.1.2",
      "difficulty": "medium",
      "question_text": "$-2^{-3}$ ifadesinin değeri kaçtır?",
      "options": [
        {
          "key": "A", "text": "$-8$", "is_correct": false,
          "misconception_tag": "MISC_EXP_NEG_POWER_AS_MULTIPLICATION",
          "misconception_detail": "Negatif kuvveti çarpmaya dönüştürme yanılgısı.",
          "recommended_subtopic_id": "top-9-exp-neg"
        },
        {
          "key": "B", "text": "$-\\frac{1}{8}$", "is_correct": true,
          "misconception_tag": null, "misconception_detail": null, "recommended_subtopic_id": null
        }
      ],
      "step_by_step_solution": "1. …\n2. …"
    }
  ]
}
```

Kurallar:
- Şıklar `A`'dan başlar ve sıralıdır (2–5 şık). Tam olarak **bir** doğru şık vardır.
- Doğru şıkta üç yanılgı alanı `null` olmalıdır. Her yanlış şıkta üçü de **zorunludur**.
- `misconception_detail` öğrenciye Hata Analizi ekranında gösterilir. Yanılgıyı yargılamadan, açıkça anlatın.
- `recommended_subtopic_id` müfredatta bulunmalıdır. Mümkünse anlatımı olan bir bölümü hedefleyin; "Konu özetine git" bağlantısı oraya gider.
- `learning_outcome` konunun kazanım listesinde bulunmalıdır.
- Aynı `misconception_tag` farklı sorularda tekrar kullanılabilir, hatta kullanılmalıdır. Hata Analizi tekrarlayan örüntüleri etiket üzerinden bulur.

## 3. Etkileşimli grafik (JSXGraph)

Konu dosyasındaki `visualizations` listesine eklenir. `section_id` verilirse grafik o bölümün anlatımının hemen altında gösterilir. Verilmezse bölümlerden sonra "Keşfet" kartında yer alır.

```json
{
  "id": "viz-9-func-slope",
  "type": "linear",
  "section_id": "top-9-func-slope",
  "title": "Eğimi ve kesişimi değiştir",
  "description": "$m$ doğrunun dikliğini belirler…",
  "bounds": [-6, 6, 6, -6],
  "sliders": [
    { "name": "m", "label": "$m$ (eğim)", "min": -4, "max": 4, "step": 0.5, "value": 1 },
    { "name": "n", "label": "$n$", "min": -4, "max": 4, "step": 0.5, "value": 1 }
  ]
}
```

| `type` | Zorunlu kaydırıcılar | Çizilenler |
| --- | --- | --- |
| `linear` | `m`, `n` | $y = mx + n$, eksen kesişimleri, eğim üçgeni |
| `parabola` | `a`, `b`, `c` | $y = ax^2 + bx + c$, gerçek kökler, tepe noktası, simetri ekseni, $\Delta$ yorumu |
| `exponential` | `a` (taban, > 0), `n` | $y = a^x$ ve $(n, a^n)$ noktası; negatif kuvvet açıklaması |
| `triangle` | `A`, `B` (derece) | Üçgen, açı yayları, $C = 180^\circ - A - B$, en uzun kenar vurgusu |

- `bounds` sırası JSXGraph'taki gibidir: `[x_min, y_max, x_max, y_min]`. Grafiğin en-boy oranı bu aralıktan hesaplanır.
- Her kaydırıcıda `min < max` ve `min ≤ value ≤ max` olmalıdır. `step > 0` olmalıdır.
- Üçgende başlangıçta `A + B < 180` olmalıdır. Öğrenci kaydırırken $C$ en az $5^\circ$ kalacak şekilde diğer açı kendiliğinden küçülür.
- Yeni bir grafik türü için hem şemaya (`content/schemas/topic.py` → `VISUALIZATION_SLIDERS`) hem de bileşene (`frontend/src/components/math/GeometryCanvas.vue`) ekleme yapılmalıdır.

## 4. OYSS takvimi

`curriculum/oyss/oyss.json` dosyasındaki `calendar` kayıtlarında `topic_ids`, ilgili sınıfın müfredatında bulunmalıdır.
Tarihleri her eğitim yılı başında resmî takvime göre güncelleyin ve `version` değerini artırın.
