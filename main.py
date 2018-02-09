#!/usr/bin/env python3
import locale
from raptic import RAPTIC


# Set locale
locale.setlocale(locale.LC_ALL, '')


def main():
   raptic = RAPTIC()
   raptic.run()


if __name__ == '__main__':
   main()
