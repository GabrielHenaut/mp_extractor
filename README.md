# mp_extractor
---

Extractor del informe de movimientos de Mergado Pago


## Usage
---

To use these you just need to put the pdf you can generate using mergado pago [link](https://www.mercadopago.com.ar/balance/reports/account_status#from-section=bitacora) from the month you want to process in the inputs directory and run the program.

The result will be in the output directory

### Setup
---

To run in a venv run the following to create it

```bash
python3 -m venv .
```

after that install all the requirements using pip.

```bash
pip install -r requirements.txt
```

To process the file execute the program passing the path to the file as a parameter (Recommeded to be in the input folder). 

```bash
python3 mp_extractor 'path_to_file'
```

