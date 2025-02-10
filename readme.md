# Setup The Project

Step 1: Create the Virtual Environment
python3 -m venv venv

Step 2: Activate the Virtual Environment
source venv/bin/activate

Step 3: Install the Required Libraries
pip install -r requirements.txt

# Run The Project

To start the FastAPI Server -
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
