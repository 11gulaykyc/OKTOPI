# OKTOPİ İçerik Deposu

Konu anlatımları, soru havuzu ve OYSS bilgileri koddan bağımsız, versiyonlu JSON dosyalarında tutulur.
Tüm dosyalar `schemas/` altındaki Pydantic modelleriyle doğrulanır:

```bash
cd backend
.venv/Scripts/python manage.py validate_content
```

| Klasör | İçerik | Şema |
| --- | --- | --- |
| `curriculum/grade-X/index.json` | Tema → konu → alt konu ağacı ve kazanımlar | `GradeCurriculumSchema` |
| `curriculum/grade-X/topics/*.json` | Konu anlatımı (bölümler, formüller, çözümlü örnekler) | `TopicSchema` |
| `curriculum/oyss/oyss.json` | OYSS bilgilendirme, takvim ve hazırlık önerileri | `OyssSchema` |
| `questions/grade-X/<konu-id>.json` | Kavram yanılgısı etiketli sorular | `QuestionFileSchema` |
| `explanations/` | (İleride) uzun, çok adımlı çözüm anlatımları | — |

## Kimlik kuralları

- Tema: `th-<sınıf>-<sıra>` → `th-9-1`
- Konu / alt konu: `top-<sınıf>-<ad>[-<alt-ad>]` → `top-9-exp`, `top-9-exp-neg`
- Soru: `q-<sınıf>-<konu>-<3 haneli no>` → `q-9-exp-001`
- Kazanım: `MAT.<sınıf>.<tema>.<no>` → `MAT.9.1.2`
- Kavram yanılgısı: `MISC_<KONU>_<AÇIKLAMA>` → `MISC_EXP_NEG_SIGN_CONFUSION`

## Soru kuralları

- Tam olarak **bir** doğru şık olmalıdır.
- Doğru şıkta `misconception_tag`, `misconception_detail`, `recommended_subtopic_id` **null** olmalıdır.
- Her yanlış şıkta bu üç alan **zorunludur**; `recommended_subtopic_id` müfredat ağacında var olmalıdır.
- `learning_outcome`, ilgili konunun kazanım listesinde bulunmalıdır.

Bir içeriği değiştirdiğinizde `version` alanını artırın (`1.0` → `1.1`).

> Not: 10–12. sınıf konu ağaçları taslaktır ve öğretim programının güncel metniyle öğretmenler tarafından doğrulanmalıdır.
