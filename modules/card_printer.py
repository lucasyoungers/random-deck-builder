#!/usr/bin/env python3

"""
This program is designed to print proxies of custom Pokémon cards.
To use, place the image files, either png or jpg, in the folder,
then run the file using python3 with PIL and fpdf installed via pip3.
"""


import os
import shutil

import requests
from fpdf import FPDF


def download(url: str) -> str:
  """Download a file from a url to the current directory."""
  r = requests.get(url)
  ext = url[url.rindex("."):] # .png, .jpg, etc
  name = url[:url.rindex(".")].rsplit("/", 2)
  name = name[1] + "_" + name[2]
  path = f".temp/{name}{ext}"
  with open(path, "wb") as file:
      file.write(r.content)
  return path


def print_pdf(files, name):
  pdf = FPDF(orientation="P", unit="in", format="Letter")

  for i, file in enumerate(files):
    if i % 9 == 0:
      pdf.add_page()
    x = 0.53 + 2.49 * (i % 3)
    y = 0.3 + 3.47 * ((i % 9) // 3)
    
    if not os.path.exists(".temp"):
      os.makedirs(".temp")
    path = download(file)
    pdf.image(path, x, y, 2.48, 3.46)
    shutil.rmtree(".temp")
  
  pdf.output(f"{name}.pdf")