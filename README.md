# ArXiv Daily Digest App

A minimal Streamlit application that generates personalized daily digests of Computer Science research papers from arXiv, with AI-powered summaries using Google Gemini Flash 2.0.

## Features

- 🔍 **Smart Search**: Query arXiv for recent CS papers using customizable keywords
- 🤖 **AI Summaries**: Generate concise, accessible summaries using Google Gemini Flash 2.0
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
- `GOOGLE_API_KEY`: Your Google Gemini API key
- `SENDGRID_API_KEY`: Your SendGrid API key (optional, for email)
- `FROM_EMAIL`: Sender email address (optional, defaults to digest@artefact.ai)

### 3. Get API Keys

**Google Gemini API:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

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

1. **Enter your email** (required for digest delivery)
2. **Customize keywords** (default: AI, ML, Computer Vision, NLP)
3. **Set paper count** (1-20 papers)
4. **Choose search timeframe** (last 1-7 days)
5. **Click "Generate & Send Digest"**

The app will:
- Search arXiv for matching papers
- Generate AI summaries for each abstract
- Display results in a clean interface
- Send formatted email digest (if configured)
- Provide download option for text export

## Configuration Options

### Keywords
Comma-separated list of research topics:
```
artificial intelligence, machine learning, computer vision, NLP, robotics
```

### Search Timeframe
- Last 1 day (default)
- Last 2 days
- Last 3 days
- Last 7 days

### Paper Limits
- Minimum: 1 paper
- Maximum: 20 papers
- Default: 5 papers

## Architecture

### Core Components
- **arxiv**: Paper search and retrieval
- **google-generativeai**: AI-powered abstract summarization
- **streamlit**: Web interface and user interaction
- **sendgrid**: Email delivery service
- **python-dotenv**: Environment variable management

### Summary Generation
The app uses Google Gemini Flash 2.0 with optimized prompts to generate:
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

**"Google API key not configured"**
- Ensure `GOOGLE_API_KEY` is set in your `.env` file
- Verify the API key is valid and has Gemini access

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
- **Google Gemini**: Check your quota and rate limits
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

**Built with ❤️ using Streamlit and Google Gemini**