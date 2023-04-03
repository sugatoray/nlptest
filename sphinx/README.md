# Building this HTML doc set locally

You can clone this repo and build and view the API documentation locally:
   
1. Change to the `sphinx` directory:

   `cd sphinx`

2. Assuming a Python 3.x environment, install dependencies:

   `pip install -r requirements.txt`

3. Build the documentation:

   `make html`

4. Run a web server:

   `python -m http.server`

5. View the doc set locally in a browser at:

   http://localhost:8000/_build/html/