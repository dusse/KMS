**Knowledge Management Pro.7** is an open-source prototype of the platform for creating, sharing, and exporting structured knowledge in a collaborative environment. The system is designed to preserve, organize, and share knowledge efficiently, making it a valuable tool for researchers, teams, and organizations.

## Key Features

- **Knowledge Cards**: Modular units containing LaTeX-formatted text, figures, references, and metadata. It supports versioning and history of changes.
- **Private and Public Collections**: Organize cards into collections that can be shared with others or kept private.  
- **Export Options**:
- Collections can be downloaded as zip files containing:
- LaTeX projects, including `.tex` files and BibTeX `.bib` files.
- Figures and other assets for offline use.
- LaTeX projects can be directly imported into Overleaf or any other LaTeX editor for further editing and compilation. 

- **Collaboration Tools**: Share collections for team collaboration while maintaining a structured and organized repository.

## Why Knowledge Management Pro.7?
The platform addresses a critical challenge in research and knowledge work: preserving comprehensive datasets and information that often get lost. By maintaining structured data through knowledge cards, this system ensures easy reuse, better organization, and availability for AI training and future projects.  

## Tech Stack  
- **Backend**: Python3, Flask, SQLAlchemy
- **Frontend**: jquery, bootstrap4, Vanilla JavaScript, HTML5, CSS3, jinja2 templates
- **Database**: PostgreSQL

## to start
1) create PostgreSQL database
2) put db info into config file [app.config.ini]
3) to run locally use python run.py
4) connect to http://127.0.0.1:5000/auth/login 
5) use admin/admin to login