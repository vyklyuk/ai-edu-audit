# -*- coding: utf-8 -*-
"""Обгортка: код збірки хабу ОП перенесено в пакет (src/ai_edu_audit/program/build.py).
Запуск з кореня проєкту: PYTHONPATH=src python3 -m ai_edu_audit.program runs/interior_b
"""
import os, runpy, sys
RUN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RUN, "..", "..", "src"))
sys.argv = [sys.argv[0], RUN]
runpy.run_module("ai_edu_audit.program.build", run_name="__main__")
