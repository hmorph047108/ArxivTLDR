# ArXiv Daily Digest App

A minimal Streamlit application that generates personalized daily digests of Computer Science research papers from arXiv, with AI-powered summaries using Google Gemini Flash 2.0 via OpenRouter.

## Features

- 🔍 **Smart Search**: Query arXiv for recent CS papers using customizable keywords
- 🤖 **AI Summaries**: Generate concise, accessible summaries using Google Gemini Flash 2.0 via OpenRouter
- 📧 **Email Delivery**: Send formatted digests via SendGrid
- 📱 **Responsive UI**: Clean, modern Streamlit interface
- 💾 **Download Options**: Export digests as text files
- ⚙️ **Configurable**: Adjust keywords, paper count, and search timeframe

## Quick Start

### 1. Clone and Install
```bash
git clone https://github.com/hmorph047108/ArxivTLDR.git
cd ArxivTLDR
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
```bash
cp .env.example .env
# Edit .env with your API keys:
```

Required variables:
- `OPENROUTER_API_KEY`: Your OpenRouter API key for Gemini Flash access
- `SENDGRID_API_KEY`: Your SendGrid API key (optional, for email)
- `OPENROUTER_SITE_URL`: Your site URL (optional, for rankings)
- `OPENROUTER_SITE_NAME`: Your site name (optional, for rankings)  
- `FROM_EMAIL`: Sender email address (optional, defaults to digest@artefact.ai)

### 3. Get API Keys

**OpenRouter API (for Gemini Flash):**
1. Sign up at [OpenRouter](https://openrouter.ai/)
2. Create an API key in your account settings
3. Add it to your `.env` file as `OPENROUTER_API_KEY`

**SendGrid API (Optional):**
1. Sign up at [SendGrid](https://sendgrid.com/)
2. Create an API key with Mail Send permissions
3. Add it to your `.env` file

### 4. Run the App
```bash
streamlit run streamlit_arxiv_digest.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### Interactive Mode (Web App)
1. **Enter your email** (required for digest delivery)
2. **Customize keywords** (default: AI, ML, Computer Vision, NLP)
3. **Select ArXiv categories** from the sidebar
4. **Set paper count** (1-20 papers)
5. **Choose search timeframe** (last 1-7 days)
6. **Configure priority sources** (institutions/companies)
7. **Click "Generate & Send Digest"**

### Daily Automation
For automated daily digests, you have several options:

**Option 1: Standalone Script**
```bash
python daily_digest.py \
  --email your@email.com \
  --keywords "AI, machine learning, robotics" \
  --categories "cs.AI,cs.LG,cs.RO" \
  --max-papers 5
```

**Option 2: Configuration File**
```bash
# Create config.json with your settings
cp config.example.json config.json
# Edit config.json with your preferences
python daily_digest.py --config config.json
```

**Option 3: Cron Job (Linux/Mac)**
```bash
# Add to crontab for daily 8 AM delivery
0 8 * * * cd /path/to/ArxivTLDR && python daily_digest.py --config config.json
```

**Option 4: GitHub Actions (Cloud)**
- Fork this repository
- Add secrets: `OPENROUTER_API_KEY`, `SENDGRID_API_KEY`
- Create `config.json` with your settings
- Enable GitHub Actions for automated daily delivery

## Configuration Options

### Smart Paper Selection

The app uses multiple strategies to identify the most relevant papers for your daily digest:

#### 1. **Category Filtering**
Choose specific ArXiv categories to monitor:
- `cs.AI` - Artificial Intelligence
- `cs.LG` - Machine Learning
- `cs.CV` - Computer Vision
- `cs.CL` - Natural Language Processing
- `cs.RO` - Robotics
- `cs.CR` - Cryptography & Security
- `cs.HC` - Human-Computer Interaction
- `cs.IR` - Information Retrieval

#### 2. **Relevance Scoring**
Papers are automatically scored based on:
- **Keyword Match**: Higher score for keywords in title vs abstract
- **Recency**: Newer papers get priority
- **Author Reputation**: Papers from top institutions/companies
- **Collaboration**: Multi-author papers often indicate larger projects

#### 3. **Priority Sources**
Boost papers from preferred institutions:
```
google, openai, anthropic, deepmind, stanford, mit, berkeley, cmu
```

#### 4. **Daily Targeting Strategies**

**For Industry Professionals:**
- Keywords: `"large language models", "production ML", "AI systems"`
- Categories: `cs.AI, cs.LG, cs.SE`
- Priority: `google, microsoft, meta, openai`

**For Researchers:**
- Keywords: `"neural networks", "optimization", "theoretical"`
- Categories: `cs.AI, cs.LG, cs.NE, cs.CC`
- Priority: `stanford, mit, berkeley, cmu`

**For Product Builders:**
- Keywords: `"applications", "deployment", "real-world"`
- Categories: `cs.AI, cs.HC, cs.IR, cs.CV`
- Priority: `google, microsoft, uber, airbnb`

### Search Configuration

#### Keywords
Comma-separated list of research topics:
```
artificial intelligence, machine learning, computer vision, NLP, robotics
```

#### Search Timeframe
- Last 1 day (default)
- Last 2 days
- Last 3 days
- Last 7 days

#### Paper Limits
- Minimum: 1 paper
- Maximum: 20 papers
- Default: 5 papers

## Architecture

### Core Components
- **arxiv**: Paper search and retrieval
- **requests**: HTTP client for OpenRouter API calls
- **streamlit**: Web interface and user interaction
- **sendgrid**: Email delivery service
- **python-dotenv**: Environment variable management

### Summary Generation
The app uses Google Gemini Flash 2.0 via OpenRouter with optimized prompts to generate:
- ≤120 word summaries
- Bullet-point format
- Focus on contribution and impact
- Jargon-free, accessible language

### Email Templates
HTML emails include:
- Formatted paper titles and authors
- AI-generated summaries
- Direct links to PDF and arXiv pages
- Clean, professional styling

## Troubleshooting

### Common Issues

**"OpenRouter API key not configured"**
- Ensure `OPENROUTER_API_KEY` is set in your `.env` file
- Verify the API key is valid and has sufficient credits

**"No papers found"**
- Try broader keywords or longer search timeframe
- Check if your keywords match CS paper terminology
- arXiv may have limited recent submissions

**"Email not sent"**
- Verify `SENDGRID_API_KEY` is correct
- Check SendGrid account status and permissions
- Ensure sender email is verified in SendGrid

**App won't start**
- Install all requirements: `pip install -r requirements.txt`
- Check Python version compatibility (3.8+)
- Verify Streamlit installation: `streamlit --version`

## Development

### Project Structure
```
ArxivTLDR/
├── streamlit_arxiv_digest.py  # Main application
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── .env                      # Your environment (create this)
└── README.md                 # This file
```

### Adding Features
The app is designed for easy extension:
- **New AI Models**: Modify `summarise_abstract()` function
- **Additional Filters**: Extend `fetch_papers()` with more criteria
- **Export Formats**: Add new download options in the UI
- **Styling**: Customize CSS in the Streamlit components

### API Limits
- **OpenRouter**: Pay-per-use model, check your credits and rate limits
- **arXiv**: Respectful usage, max 3 requests per second
- **SendGrid**: Free tier allows 100 emails/day

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Check the troubleshooting section above
- Review your API key configuration
- Verify environment variable setup

---

**Built with ❤️ using Streamlit and Google Gemini via OpenRouter**