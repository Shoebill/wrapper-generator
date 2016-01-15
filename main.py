import cidl
import sys
import os.path

JAVA_TYPES_IN = {
  'int'    : 'int',
  'bool'   : 'boolean',
  'float'  : 'float',
  'string' : 'String',
}

JAVA_TYPES_OUT = {
  'int'    : 'ReferenceInt',
  'float'  : 'ReferenceFloat',
  'string' : 'ReferenceString',
}

JAVA_API_RETURNTYPES = {
    'int' : 'ReturnType.INTEGER',
    'float' : 'ReturnType.FLOAT',
    'string' : 'ReturnType.STRING'
}

C_SHORT_FORMS = {
    'int' : 'i',
    'float' : 'f',
    'string' : 's'
}

FILE_NAME = ""

class Parameter(cidl.Parameter):
  def __init__(self, type, name, default=None, attrlist=None):
    cidl.Parameter.__init__(self, type, name, default, attrlist)

  @property
  def java_type(self):
    try:
      if self.is_ref:
        return JAVA_TYPES_OUT[self.type]
      else:
        return JAVA_TYPES_IN[self.type]
    except KeyError:
      if self.is_ref:
        return '%s *' % self.type
      else:
        return self.type

  @property
  def is_ref(self):
    return self.is_out or self.type == 'string'


def generateJavaFunctions(filename, idl):

    validFunctions = [x for x in idl.functions if x.has_attr("native")]

    result = "import net.gtaun.shoebill.amx.AmxCallable;\n" \
             "import net.gtaun.shoebill.amx.AmxInstance;\n" \
             "import java.util.HashMap;\n" \
             "import net.gtaun.shoebill.amx.types.*;\n\n" \
             "public class Functions {\n\n" \
             "\tprivate static HashMap<String, AmxCallable> functions = new HashMap<>();\n\n" \
             "\tpublic static void registerFunctions(AmxInstance instance) {\n"

    for function in validFunctions:
        result += "\t\tfunctions.put(\"" + function.name + "\", instance.getNative(\"" + function.name + "\", " + JAVA_API_RETURNTYPES[function.type] + "));\n"

    result += "\t}\n\n"

    for function in validFunctions:
        result += "\tpublic static " + JAVA_TYPES_IN[function.type] + " " + function.name + "("
        if function.params:
            for index,parameter in enumerate(function.params):
                result += parameter.java_type +  " " + parameter.name
                if index + 1 < len(function.params):
                    result += ", "
        result += ") {\n" \
                  "\t\treturn (" + function.type + ") functions.get(\"" + function.name + "\").call("
        for index,parameter in enumerate(function.params):
            result += parameter.name
            if index + 1 < len(function.params):
                result += ", "
        result += ");\n\t}\n\n"

    result += "}"

    with open(filename, 'w') as file:
        file.write(result)
    return

def generateJavaCallbacks(filename, idl):
    validCallbacks = [x for x in idl.functions if x.has_attr("callback")]

    result = "import net.gtaun.shoebill.amx.AmxInstanceManager;\n\n" \
             "public class Callbacks {\n\n" \
             "\tpublic static void registerHandlers(AmxInstanceManager instanceManager) {\n"

    for index,function in enumerate(validCallbacks):
        result += "\t\tinstanceManager.hookCallback(\"" + function.name + "\", amxCallEvent -> {\n"
        if function.params:
            for paramIndex,parameter in enumerate(function.params):
                result += "\t\t\t" + parameter.java_type + " " + parameter.name + " = (" + parameter.java_type + ") amxCallEvent.getParameters()[" + str(paramIndex) + "];\n"

            result += "\t\t\t//TODO: Add your event logic for " + function.name + " here\n" \
                        "\t\t}, \""

        for paramIndex,parameter in enumerate(function.params):
            result += C_SHORT_FORMS[parameter.type]

        result += "\");\n\n"

    result += "\t}\n\n\tpublic static void unregisterHandlers(AmxInstanceManager instanceManager) {\n"

    for function in validCallbacks:
        result += "\t\tinstanceManager.unhookCallback(\"" + function.name + "\");\n"

    result += "\t}\n}"
    with open(filename, 'w') as file:
        file.write(result)

    return

def generateJavaConstants(filename, idl):
    result = "public class Constants {\n\n"

    for constant in idl.constants:
        result += "\tpublic static final " + JAVA_TYPES_IN[constant.type] + " " + constant.name + " = " + str(constant.value.data) + ";\n"

    result += "\n}"

    with open(filename, 'w') as file:
        file.write(result)
    return

def doesFileExists():
    return os.path.exists(FILE_NAME)

def startParsing():
    try:
        idlparser = cidl.Parser(param_class=Parameter)
        idl = idlparser.parse(open(FILE_NAME, 'r').read())

        generateJavaFunctions("Functions.java", idl)
        generateJavaCallbacks("Callbacks.java", idl)
        generateJavaConstants("Constants.java", idl)

        print("Parsing process has been finished successfully. " + str(len(idl.functions)) + " functions / callbacks and " + str(len(idl.constants)) + " constants parsed.")

    except cidl.Error as e:
        print(e)
    return

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 2:
        print("Unknown count of arguments detected. Please only give 1 argument (the .idl file)")
        return

    global __location__
    global FILE_NAME
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    FILE_NAME = os.path.join(__location__, sys.argv[1])

    print("******************************************")
    print("* Shoebill functions & callbacks parser  *")
    print("* Author: Marvin Haschker (123marvin123) *")
    print("* Credits to: Zeex                       *")
    print("******************************************")

    fileExists = doesFileExists()
    print("Checking whether the " + FILE_NAME + " file is present... " + str(fileExists))
    if fileExists == False:
        print("\033[91mERROR:\033[0m The " + FILE_NAME + " file does not exists. Exiting...")
        return
    else:
        print("The " + FILE_NAME + " file has been found. Loading and parsing file...")
        startParsing()

    return

if __name__ == "__main__":
    main()