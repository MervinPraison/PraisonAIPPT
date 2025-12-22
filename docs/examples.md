---
layout: default
title: "Examples and Templates - PraisonAI PPT"
description: "Collection of examples and templates for creating presentations"
---

# Examples and Templates

## 📋 Built-in Examples

### Available Examples
```bash
# List all examples
praisonaippt --list-examples

# Use an example
praisonaippt --use-example tamil_verses
praisonaippt --use-example sample_verses
```

## 🎯 Example Templates

### Basic Template
```json
{
  "presentation_title": "Your Presentation Title",
  "presentation_subtitle": "Your Subtitle",
  "sections": [
    {
      "section": "Section Name",
      "verses": [
        {
          "reference": "Book Chapter:Verse (Version)",
          "text": "The actual verse text here.",
          "highlights": ["word1", "phrase to highlight"]
        }
      ]
    }
  ]
}
```

### Sunday Service Template
```json
{
  "presentation_title": "Sunday Service - [Date]",
  "presentation_subtitle": "[Church Name]",
  "sections": [
    {
      "section": "Opening Worship",
      "verses": [
        {
          "reference": "Psalm 100:1-2 (KJV)",
          "text": "Make a joyful noise unto the Lord, all ye lands. Serve the Lord with gladness: come before his presence with singing.",
          "highlights": ["joyful noise", "gladness", "singing"]
        }
      ]
    },
    {
      "section": "Main Message",
      "verses": [
        {
          "reference": "John 3:16 (KJV)",
          "text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
          "highlights": ["God", "loved", "everlasting life"],
          "large_text": {"everlasting life": 200}
        }
      ]
    },
    {
      "section": "Closing Prayer",
      "verses": [
        {
          "reference": "Philippians 4:7 (KJV)",
          "text": "And the peace of God, which passeth all understanding, shall keep your hearts and minds through Christ Jesus.",
          "highlights": ["peace of God", "keep your hearts"]
        }
      ]
    }
  ]
}
```

### Bible Study Template
```json
{
  "presentation_title": "Bible Study - [Topic]",
  "presentation_subtitle": "Deep Dive into Scripture",
  "sections": [
    {
      "section": "Introduction",
      "verses": [
        {
          "reference": "2 Timothy 2:15 (KJV)",
          "text": "Study to shew thyself approved unto God, a workman that needeth not to be ashamed, rightly dividing the word of truth.",
          "highlights": ["Study", "approved unto God", "word of truth"]
        }
      ]
    },
    {
      "section": "Main Passage",
      "verses": [
        {
          "reference": "[Book] [Chapter]:[Verse] (KJV)",
          "text": "Your main study passage here...",
          "highlights": ["key concepts", "important phrases"]
        },
        {
          "reference": "[Book] [Chapter]:[Verse] (KJV)",
          "text": "Additional supporting verses...",
          "highlights": ["supporting concepts"]
        }
      ]
    },
    {
      "section": "Application",
      "verses": [
        {
          "reference": "James 1:22 (KJV)",
          "text": "But be ye doers of the word, and not hearers only, deceiving your own selves.",
          "highlights": ["doers of the word", "not hearers only"]
        }
      ]
    }
  ]
}
```

### Easter Template
```json
{
  "presentation_title": "He is Risen!",
  "presentation_subtitle": "Celebrating the Resurrection of Jesus Christ",
  "sections": [
    {
      "section": "The Empty Tomb",
      "verses": [
        {
          "reference": "Matthew 28:6 (KJV)",
          "text": "He is not here: for he is risen, as he said. Come, see the place where the Lord lay.",
          "highlights": ["risen", "Lord"]
        }
      ]
    },
    {
      "section": "The Victory",
      "verses": [
        {
          "reference": "1 Corinthians 15:55-57 (KJV)",
          "text": "O death, where is thy sting? O grave, where is thy victory? The sting of death is sin; and the strength of sin is the law. But thanks be to God, which giveth us the victory through our Lord Jesus Christ.",
          "highlights": ["victory", "Lord Jesus Christ"],
          "large_text": {"victory": 200}
        }
      ]
    },
    {
      "section": "The Promise",
      "verses": [
        {
          "reference": "John 11:25 (KJV)",
          "text": "Jesus said unto her, I am the resurrection, and the life: he that believeth in me, though he were dead, yet shall he live:",
          "highlights": ["resurrection", "life"],
          "large_text": {"resurrection": 200}
        }
      ]
    }
  ]
}
```

### Christmas Template
```json
{
  "presentation_title": "The Gift of Christmas",
  "presentation_subtitle": "Celebrating the Birth of Our Savior",
  "sections": [
    {
      "section": "The Prophecy",
      "verses": [
        {
          "reference": "Isaiah 9:6 (KJV)",
          "text": "For unto us a child is born, unto us a son is given: and the government shall be upon his shoulder: and his name shall be called Wonderful, Counsellor, The mighty God, The everlasting Father, The Prince of Peace.",
          "highlights": ["child is born", "Prince of Peace"],
          "large_text": {"Prince of Peace": 200}
        }
      ]
    },
    {
      "section": "The Birth",
      "verses": [
        {
          "reference": "Luke 2:11 (KJV)",
          "text": "For unto you is born this day in the city of David a Saviour, which is Christ the Lord.",
          "highlights": ["Saviour", "Christ the Lord"]
        }
      ]
    },
    {
      "section": "The Meaning",
      "verses": [
        {
          "reference": "John 3:16 (KJV)",
          "text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
          "highlights": ["God", "loved", "everlasting life"]
        }
      ]
    }
  ]
}
```

## 🎨 Advanced Examples

### Multi-language Support
```json
{
  "presentation_title": "தமிழ் வேத வசனங்கள்",
  "presentation_subtitle": "Tamil Bible Verses",
  "sections": [
    {
      "section": "அன்பு",
      "verses": [
        {
          "reference": "யோவான் 3:16",
          "text": "தேவன் உலகை இவ்வளவு அன்பித்தார் என்பதால், தன் ஒரே புத்திரனை கொடுத்தார்; அவனை நம்புகிற யாரும் அழியாமல் நித்திய ஜீவனைப் பெறுவார்கள் என்று.",
          "highlights": ["அன்பித்தார்", "நித்திய ஜீவனை"]
        }
      ]
    }
  ]
}
```

### Custom Formatting
```json
{
  "presentation_title": "Custom Formatting Example",
  "presentation_subtitle": "Advanced Features Demonstration",
  "sections": [
    {
      "section": "Text Formatting",
      "verses": [
        {
          "reference": "Psalm 23:1 (KJV)",
          "text": "The Lord is my shepherd; I shall not want.",
          "highlights": ["Lord", "shepherd"],
          "large_text": {"shepherd": 180}
        },
        {
          "reference": "Psalm 23:4 (KJV)",
          "text": "Yea, though I walk through the valley of the shadow of death, I will fear no evil: for thou art with me; thy rod and thy staff they comfort me.",
          "highlights": ["valley of the shadow of death", "fear no evil"],
          "large_text": {
            "valley of the shadow of death": 160,
            "fear no evil": 180
          }
        }
      ]
    }
  ]
}
```

## 🔧 Usage Examples

### CLI Examples
```bash
# Use Easter template
praisonaippt --use-example easter_verses --convert-pdf

# Create from custom file
praisonaippt -i sunday_service.json -o "Service_2024-12-22.pptx"

# Batch create multiple services
for service in morning evening; do
  praisonaippt -i "${service}_service.json" -o "${service}_service.pptx" --convert-pdf
done
```

### Python API Examples
```python
from praisonaippt import create_presentation, load_verses_from_dict

# Create custom presentation programmatically
data = {
    "presentation_title": "Dynamic Presentation",
    "sections": [
        {
            "section": "Generated Content",
            "verses": [
                {
                    "reference": "Philippians 4:13 (KJV)",
                    "text": "I can do all things through Christ which strengtheneth me.",
                    "highlights": ["all things", "Christ strengtheneth"]
                }
            ]
        }
    ]
}

result = create_presentation(data, convert_to_pdf=True)
print(f"Created: {result}")
```

## 📚 Template Creation Tips

### Best Practices
1. **Consistent Formatting**: Use the same Bible version throughout
2. **Logical Grouping**: Organize verses by themes or sections
3. **Highlight Key Points**: Use highlights for emphasis
4. **Large Text Sparingly**: Use for main concepts only
5. **Reference Format**: Include version (KJV, ESV, etc.)

### Naming Conventions
```bash
# Good filenames
sunday_service_2024-12-22.json
easter_celebration.json
bible_study_john_chapter_3.json
tamil_verses.json

# Avoid
verses.json (too generic)
file1.json (not descriptive)
```

### File Organization
```
presentations/
├── templates/
│   ├── sunday_service.json
│   ├── bible_study.json
│   └── special_events.json
├── 2024/
│   ├── 01_january/
│   ├── 02_february/
│   └── 12_december/
└── languages/
    ├── tamil/
    └── spanish/
```

## 🎯 Next Steps

- [Installation Guide]({{ '/installation' | relative_url }})
- [Command Reference]({{ '/commands' | relative_url }})
- [Python API Documentation]({{ '/python-api' | relative_url }})

---

**Need help?** [Open an issue on GitHub](https://github.com/MervinPraison/PraisonAIPPT/issues)
