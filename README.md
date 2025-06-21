# StockageCloud

A modern, secure cloud storage web application built with Flask that allows users to upload, store, and manage their files with a beautiful, responsive interface.

## Features

- 🔐 **User Authentication**: Secure login and registration system with password hashing
- 📁 **File Management**: Upload, download, and delete files with security features
- 🎨 **Modern UI**: Clean, responsive design with drag-and-drop functionality
- 📱 **Mobile Friendly**: Optimized for all device sizes
- 🔒 **Secure Storage**: Files are stored securely with user isolation and integrity checks
- ⚡ **Real-time Feedback**: Instant notifications and loading states
- 🛡️ **File Security**: Unique filenames, type validation, and corruption detection

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd StockageCloud
```

### 2. Install Dependencies

Install the required Python packages:

```bash
pip install flask
```

Or using the requirements file:

```bash
pip install -r requirements.txt
```

## Database Setup

### 1. Initialize the Database

Run the following command to create and initialize the database:

```bash
flask --app app.py init-db
```

This command will:
- Create the `database.db` file if it doesn't exist
- Set up the necessary tables for users and files
- Initialize the database schema

## Running the Application

### 1. Start the Flask Server

Run the application with:

```bash
flask --app app.py run
```

### 2. Access the Application

After running the command, you should see output similar to:

```
 * Serving Flask app 'app.py'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```

Click on the URL link (`http://127.0.0.1:5000`) or copy and paste it into your web browser.

## Usage

### 1. Registration
- Navigate to the registration page
- Create a new account with your email and password
- **Your password will be securely hashed before storage**

### 2. Login
- Use your registered credentials to log in
- You'll be redirected to your personal dashboard

### 3. File Management
- **Upload Files**: Drag and drop files or click to select them
- **Download Files**: Click the download button on any file
- **Delete Files**: Click the delete button to remove files (with confirmation)

## Project Structure

```
StockageCloud/
├── app.py              # Main Flask application
├── db.py               # Database operations
├── schema.sql          # Database schema
├── database.db         # SQLite database (created after init-db)
├── static/             # Static assets
│   ├── css/
│   │   └── styles.css  # Main stylesheet
│   └── js/
│       ├── dashboard.js # Dashboard functionality
│       ├── login.js     # Login page scripts
│       └── register.js  # Registration scripts
├── templates/          # HTML templates
│   ├── dashboard.html  # User dashboard
│   ├── index.html      # Landing page
│   ├── login.html      # Login page
│   ├── mainpage.html   # Main page
│   └── register.html   # Registration page
└── uploads/            # File storage directory
```

## Configuration

The application uses default Flask configuration. Key settings:

- **Database**: SQLite database (`database.db`)
- **File Storage**: `uploads/` directory
- **Port**: 5000 (default Flask port)
- **Debug Mode**: Off (for production)
- **Max File Size**: 50MB
- **Allowed File Types**: Common document, image, audio, video, and archive formats

## Security Features

- **Password Hashing**: All passwords are hashed using Werkzeug's PBKDF2 with SHA256
- **File Security**: 
  - Unique UUID-based filenames prevent overwrites
  - Original filenames are sanitized and preserved
  - File type validation prevents malicious uploads
  - SHA-256 file integrity checks detect corruption
  - File size limits prevent abuse
- User session management
- File access isolation (users can only access their own files)
- CSRF protection
- Secure file upload handling
- Protection against SQL injection

## Supported File Types

- **Documents**: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT
- **Images**: PNG, JPG, JPEG, GIF, BMP, SVG
- **Audio**: MP3, WAV, FLAC, AAC, OGG
- **Video**: MP4, AVI, MOV, WMV, FLV
- **Archives**: ZIP, RAR, 7Z, TAR, GZ

## Troubleshooting

### Common Issues

1. **Port already in use**: If port 5000 is busy, Flask will automatically try the next available port
2. **Database errors**: Run `flask --app app.py init-db` to recreate the database
3. **Permission errors**: Ensure you have write permissions in the project directory

### Development Mode

For development with auto-reload:

```bash
flask --app app.py run --debug
```

## Browser Compatibility

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## License

This project is open source and available under the [MIT License](LICENSE).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Note**: This is a development application. For production use, consider implementing additional security measures, using a production WSGI server, and setting up proper environment variables for sensitive configuration. 