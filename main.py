import os.path
import string
import re
import sys

FILE_NAME = ""
REGEX_NATIVE = "^native (.*?)\:?([a-zA-Z_]*)\(([a-zA-Z&,:\[\] ]*)\)$"
REGEX_CALLBACK = "^forward ([a-zA-Z_]*)\(([a-zA-Z,_: ]*)\)$"
REGEX_DEFINITION = "^#define ([a-zA-Z_]*) * \(?(.*?)\)?$"
REGEX_PARAMETER = "^([a-zA-Z&]*)\:?(.*)$"
JAVA_PYTHON_TYPE_MAP = {"Int": "int", "String": "String", "Float": "float", "bool": "boolean"}
JAVA_PYTHON_C_TYPES = {"Int": "i", "String": "s", "Float" : "f"}

def getJavaType(parameter):
    if parameter.isReference == False:
        return JAVA_PYTHON_TYPE_MAP[parameter.type]
    else:
        JAVA_PYTHON_REFERENCE_TYPE_MAP = {"Int": "ReferenceInt", "Float": "ReferenceFloat", "String": "ReferenceString"}
        return JAVA_PYTHON_REFERENCE_TYPE_MAP[parameter.type]

class Parameter:

    def __init__(self, name, type, isReference):
        self.name = name
        self.type = type
        self.isReference = isReference

    def __str__(self):
        result = ""
        if self.isReference:
            result += "&"
        result += self.type + ":" + self.name
        return result

class Native:

    def __init__(self, name, parameters, returntype):
        self.name = name
        self.parameters = parameters
        self.returntype = returntype

    def __str__(self):

        parameterString = ""
        for index,param in enumerate(self.parameters):
            parameterString += str(param)
            if index + 1 < len(self.parameters):
                parameterString += ", "

        return "Native: " + self.name + "(" + parameterString + ")"
        
class Callback:

    def __init__(self, name, parameters):
        self.name = name
        self.parameters = parameters

    def __str__(self):
        parameterString = ""
        for index,param in enumerate(self.parameters):
            parameterString += str(param)
            if index + 1 < len(self.parameters):
                parameterString += ", "
        return "Callback: " + self.name + "(" + parameterString + ")"
        
class Definition:

    def __init__(self, name, value, type):
        self.name = name
        self.value = value
        self.type = type

    def __str__(self):
        return "Definition: " + self.name + " " + self.value + " (" + self.type + ")"
    
def parseParameter(parameter):
    result = re.match(REGEX_PARAMETER, parameter)
    if result:
        paramType = result.group(1)
        paramName = result.group(2)
        if len(paramName) > 0:
            isRef = False
            if paramType.startswith("&"):
                paramType = paramType[1:]
                isRef = True
            if paramName == "[]":
                paramName = paramType
                paramType = "String"
            return Parameter(paramName, paramType, isRef)
        else:
            isRef = False
            if paramType.startswith("&"):
                paramType = paramType[1:]
                isRef = True
            return Parameter(paramType, "Int", isRef)
    return

def parseNative(line):
    result = re.match(REGEX_NATIVE, line)
    if result:
        returntype = result.group(1)
        if returntype == "":
            returntype = "Int"
        name = result.group(2)
        paramParts = [x for x in string.split(result.group(3), ',')]
        parameters = []
        for param in paramParts:
            parameters.append(parseParameter(param.strip()))
        native = Native(name, parameters, returntype)
        return native
    return None

def parseCallback(line):
    result = re.match(REGEX_CALLBACK, line)
    if result:
        name = result.group(1)
        paramParts = [x for x in string.split(result.group(2), ',')]
        parameters = []
        for param in paramParts:
            parameters.append(parseParameter(param.strip()))
        callback = Callback(name, parameters)
        return callback
    return None

def parseDefinition(line):
    result = re.match(REGEX_DEFINITION, line)
    if result:
        name = result.group(1)
        value = result.group(2)
        type = "String"
        if is_number(value) == True:
            type = "Int"
        definition = Definition(name, value, type)
        return definition
    return None

def parseFile(content):
    lines = string.split(content, '\n')
    lines[:] = [x for x in lines if x.startswith("native") or x.startswith("forward") or x.startswith("#define")]
    natives = []
    callbacks = []
    definitions = []
    for index,line in enumerate(lines):
        if line.endswith(";"):
            lines[index] = line[:-1]
            native = parseNative(lines[index])
            if native is not None:
                natives.append(native)
            callback = parseCallback(lines[index])
            if callback is not None:
                callbacks.append(callback)
        definition = parseDefinition(lines[index])
        if definition is not None:
            definitions.append(definition)
    generateJavaNativeFile("Functions.java", natives)
    generateJavaDefinitionFile("Definitions.java", definitions)
    generateJavaCallbackFile("Callbacks.java", callbacks)

    print("All files has been generated. " + str(len(natives)) + " native function(s), " + str(len(callbacks)) + " callback(s) and " + str(len(definitions)) + " definition(s) have been exported.")
    return

def generateJavaNativeFile(filename, natives):
    result = "import net.gtaun.shoebill.amx.AmxCallable;\n" \
             "import net.gtaun.shoebill.amx.AmxInstance;\n" \
             "import java.util.HashMap;\n" \
             "import net.gtaun.shoebill.amx.types.*;\n\n" \
             "public class Functions {\n" \
             "\n" \
             "\tprivate static String[] functionList = new String[]{\n"

    count = 0

    for index,native in enumerate(natives):
        if count == 0:
            result += "\t\t"
        result += "\"" + native.name + "\""
        if index + 1 == len(natives):
            result += "\n\t};\n\n"
            break
        if count < 3:
            result += ", "
        else:
            result += ",\n\t\t"
            count = 0
        count += 1

    result += "\tprivate static HashMap<String, AmxCallable> functions = new HashMap<>();\n\n" \
              "\tpublic static void registerFunctions(AmxInstance instance) {\n" \
              "\t\tfor(String function : functionList) {\n" \
              "\t\t\tAmxCallable callable = instance.getNative(function);\n" \
              "\t\t\tif(callable != null) functions.put(function, callable);\n" \
              "\t\t\telse System.out.println(\"Function \" + function + \" has not been found.\");\n" \
              "\t\t}\n" \
              "\t}\n\n"

    for index,native in enumerate(natives):
        result += "\tpublic static " + JAVA_PYTHON_TYPE_MAP[native.returntype] + " " + native.name + "("
        for paramIndex,param in enumerate(native.parameters):
            result += getJavaType(param) + " " + param.name
            if paramIndex + 1 < len(native.parameters):
                result += ", "
            else:
                result += ") {\n"
        result += "\t\treturn (" + JAVA_PYTHON_TYPE_MAP[native.returntype] + ") functions.get(\"" + native.name + "\").call("
        for paramIndex,param in enumerate(native.parameters):
            result += param.name
            if paramIndex + 1 < len(native.parameters):
                result += ", "
            else:
                result += ");\n"
        result += "\t}\n\n"
    result += "}"

    with open(filename, "w") as file:
        file.write(result)
    return

def generateJavaCallbackFile(filename, callbacks):
    result = "import net.gtaun.shoebill.amx.AmxInstanceManager;\n\n" \
             "public class Callbacks {\n\n" \
             "\tpublic static void registerHandlers(AmxInstanceManager instanceManager) {\n\n"

    for index,callback in enumerate(callbacks):
        result += "\t\tinstanceManager.hookCallback(\"" + callback.name + "\", amxCallEvent -> {\n"
        for paramIndex,parameter in enumerate(callback.parameters):
            javaType = getJavaType(parameter)
            result += "\t\t\t" + javaType + " " + parameter.name + " = (" + javaType + ") amxCallEvent.getParameters()[" + str(paramIndex) + "];\n"
            if paramIndex + 1 == len(callback.parameters):
                result += "\t\t\t//TODO: Add your event logic for " + callback.name + " here\n" \
                          "\t\t}, \""

        for paramIndex,parameter in enumerate(callback.parameters):
            cType = JAVA_PYTHON_C_TYPES[parameter.type]
            result += cType

        result += "\");\n\n"

    result += "\t}\n\n" \
              "\tpublic static void unregisterHandlers(AmxInstanceManager instanceManager) {\n"

    for index,callback in enumerate(callbacks):
        result += "\t\tinstanceManager.unhookCallback(\"" + callback.name + "\");\n"

    result += "\t}\n}"

    with open(filename, "w") as file:
        file.write(result)
    return

def generateJavaDefinitionFile(filename, definitions):
    result = "public class Definitions {\n\n"

    for index,definition in enumerate(definitions):
        result += "\tpublic static final " + JAVA_PYTHON_TYPE_MAP[definition.type] + " " + definition.name + " = "
        if definition.type == "String":
            result += "\"" + definition.value + "\""
        else:
            result += definition.value
        result += ";\n"

    result += "\n}"

    with open(filename, "w") as file:
        file.write(result)
    return

def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def loadFile():
    with open(FILE_NAME) as f:
        return f.read()

def doesIncludeExists():
    return os.path.exists(FILE_NAME)

def main():

    if len(sys.argv) < 2 or len(sys.argv) > 2:
        print("Unknown count of arguments detected. Please only give 1 argument (the .inc file)")
        return

    global __location__
    global FILE_NAME
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    FILE_NAME = os.path.join(__location__, sys.argv[1])

    print("******************************************")
    print("* Shoebill functions & callbacks parser  *")
    print("* Author: Marvin Haschker (123marvin123) *")
    print("******************************************")
    includePresent = doesIncludeExists()
    print("Checking whether the " + FILE_NAME + " file is present... " + str(includePresent))
    if includePresent == False:
        print("\033[91mERROR:\033[0m The " + FILE_NAME + " file does not exists. Exiting...")
        return
    else:
        print("The " + FILE_NAME + " file has been found. Loading and parsing file...")
        parseFile(loadFile())

if __name__ == "__main__":
    main()