# extractor.py
# Este script es ejecutado DENTRO de Ghidra en modo headless (postScript).
# Corre bajo el entorno Jython (Python 2.7) embebido en Ghidra,
# por lo que NO tiene acceso a las librerias del Python 3 del proyecto principal.
#
# Uso (via analyzeHeadless):
#   analyzeHeadless <project_dir> <project_name> -import <binary> \
#       -postScript extractor.py <output_json_path> -scriptPath ghidra_scripts/

import json

from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor


def extract_functions():
    functions = []
    function_manager = currentProgram.getFunctionManager()
    for func in function_manager.getFunctions(True):
        functions.append({
            "name": func.getName(),
            "entry_point": str(func.getEntryPoint()),
            "signature": str(func.getSignature()),
        })
    return functions


def extract_decompiled_code(functions_limit=None):
    decompiler = DecompInterface()
    decompiler.openProgram(currentProgram)
    monitor = ConsoleTaskMonitor()

    decompiled = []
    function_manager = currentProgram.getFunctionManager()
    functions = list(function_manager.getFunctions(True))
    if functions_limit:
        functions = functions[:functions_limit]

    for func in functions:
        result = decompiler.decompileFunction(func, 60, monitor)
        if result.decompileCompleted():
            decompiled.append({
                "name": func.getName(),
                "entry_point": str(func.getEntryPoint()),
                "code": result.getDecompiledFunction().getC(),
            })

    decompiler.dispose()
    return decompiled


def save_output(data, output_path):
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


def run():
    args = getScriptArgs()
    output_path = args[0] if len(args) > 0 else "extractor_output.json"

    data = {
        "program_name": currentProgram.getName(),
        "functions": extract_functions(),
        "decompiled": extract_decompiled_code(),
    }
    save_output(data, output_path)
    print("[extractor] Output written to: " + output_path)


run()
