## CSCI 360 - Project 1
## Author: Emanuel Aracena
## Created on September 28, 2019

## 
## Using code from file 'project_source_code_analyzer.py' given by Professor Xiaojie Zhang
##

import sys
import json


# Global declaration count to keep track of all declarations across functions
declaration = 1

# int total(int num)
def read_head(line):
    words = [""]
    i = 0
    for char in line:
        if char != ' ' and char != '(' and char != ')' and char != ',':
            words[i] = words[i] + str(char)
            #print(words)
        else:
            words = words + [""]
            i = i + 1
            if char == ")":
                break
    return words


# int sum=0;
def read_declaration(line):
    global declaration
    words = ["", "", ""]
    i = 0
    for char in line:
        if char != ' ' and char != '=' and char != ';':
            words[i] = words[i] + str(char)
        else:
            i = i + 1
    declaration = declaration + 1
    obj = {
        "codeType": "declaration",
        "dataType": words[0],
        "dataName": words[1],
        "dataValue": words[2],
        "address": -(declaration*4)
    }

    return obj


# sum=sum+num;
def read_logic(line):
    words = ["", "", "",""]
    i = 0
    for char in line:
        if char == '+' or char == '-' or char == '/':
            i = i + 1
            words[i] = str(char)
            i = i + 1
        elif char != '=' and char != ';':
            words[i] = words[i] + str(char)
        else:
            i = i + 1
    obj = {
        "codeType": "logicOperation",
        "destination": words[0],
        "operand1": words[1],
        "operator": words[2],
        "operand2": words[3]
    }
    return obj


# read instructions recursively
def read_instruction(i, segment):
    instruction = []
    while i < len(segment):
        line = segment[i]
        if line == "}":
            break
        if line.startswith("int"):
            instruction.append(read_declaration(line))
            i = i + 1
        elif line.startswith("for"):
            result = read_for_loop(i, segment)
            instruction.append(result["for"])
            i = result["i"]
        elif line.startswith("return"):
            instruction.append(line)
            i = i + 1
        else:
            instruction.append(read_logic(line))
            i = i + 1
    return {"i": i+1, "statement": instruction}


# for(int i=0;i<num;i=i+1)
def read_for_loop(i, segment):
    line = segment[i]
    header = line[4:-2].split(';')
    obj = {"codeType": "for",
           "initialization": read_declaration(header[0]+";"),
           "termination": header[1],
           "increment": read_logic(header[2]+";"),
           "statement": []
           }
    i = i + 1
    result = read_instruction(i, segment)
    obj["statement"] = result["statement"]
    return {"i": result["i"], "for": obj}


# Read from file into line seperated strings in list called source
def read_source(filename):
  with open(filename) as file:
    source = file.readlines()
  
  # remove trailing whitespace and newlines
  source = [x.rstrip('\n') for x in source]
  source = [x.rstrip('\t') for x in source]
  source = [x.rstrip(' ') for x in source]  
  source = [x.lstrip('\t') for x in source]
  source = [x.lstrip(' ') for x in source]
  
  # remove all empty items
  source = [x for x in source if x != '']  

  #print(source)
  return source


# Main translation function
def translate(functions):
  
  print("")
  print("")

  for function in functions:
    # Print function name
    print(function["functionName"] + ": ")

    # Create scope hash table to keep track of all declared variables/parameters
    scope = {}

    # Add parameters to scope
    for parameter in function["parameter"]:
      scope[parameter["dataName"]] =   "+" + str(-1*parameter["address"])

    # translate instructions
    for instruction in function["instruction"]:
      if "return" in instruction:
        value = instruction.split(" ")[1].strip(";")
        if value in scope:
          print("\tmov\teax, DWORD PTR[rbp" + str(scope[value]) + "]")
        else:
          print("\tmov\teax, " + str(value))
        print("\tpop rbp")
        print("\tret")
        break
      if instruction["codeType"] == "declaration":
        #print(instruction)
        # add declaration to the scope
        scope[ instruction[ "dataName" ] ] = instruction["address"] 
        #print(scope)
        # if declaration instantly assigns value, translate immediately
        if instruction["dataValue"] != "":
          print("\tmov\tDWORD PTR [rbp" + instruction["address"].strip(' ') + "], " + instruction["dataValue"] )
            
      if instruction["codeType"] == "logicOperation":
        
        # Set the assembly operator
        operator = ""
        if instruction["operator"] == "+":
          operator = "add"
           
        if instruction["operator"] == "-":
          operator = "sub"

        if instruction["operator"] == "":
          if "(" in instruction["operand1"]:
            operator = "call"
          else:
            operator = "mov"

        # Print the assembly instruction 
        if operator == "add" or operator == "sub":
          if instruction["operand2"].strip(' ') in scope:
            # mov eax, mem[operand2]
            # op mem[dest], eax
            print("\tmov\teax, DWORD PTR[rbp"+ str(scope[instruction["operand2"].strip(" ")]) + "]")
            print("\t" + operator + "\tDWORD PTR[rbp" + str(scope[instruction["destination"].strip(' ')]) + "], eax" )
          else:
            # op mem[dest], num
            print("\t" + operator + "\tDWORD PTR[rbp" + str(scope[instruction["destination"].strip(' ')]) + "], " + instruction["operand2"].strip(" "))
     
        if operator == "mov":
          print("\t" + operator + "\tDWORD PTR[rbp" + str(scope[instruction["destination"].strip(' ')]) + "], " + instruction["operand1"] )
        
        if operator == "call":
          # count number of arguments
          function_call = instruction["operand1"].strip(" ")

          # Split into substrings, until arguments seperated by commas remain,
          # then find the length of the list when split by commas
          # for example: f1(a, b, c) turns into a| b | c which has length 3
          num_of_args = len(function_call.split("(")[1].strip(")").split())
          arguments = function_call.split("(")[1].strip(")").split()

          # Theres only six registers for argument calling:
          # rdi, rsi, rdx, rcx, r8, r9
          # the rest are pushed to stack
          registers = ["rsi", "rdx", "rcx", "r8", "r9"]

          num_of_args = num_of_args - 1
          while num_of_args >= 0:
            if num_of_args > 4:
              # Push onto stack
              print("\tmov\tedi, DWORD PTR[rbp" + scope[arguments[num_of_args].strip(" ")] + "]") 
              print("\tpush\trdi")
            else:
              # Use registers
              print("\tmov\t"+ registers[num_of_args] + ", DWORD PTR[rbp" + str(scope[ arguments[num_of_args].strip(" ").strip(",")]) + "]")
            
            num_of_args = num_of_args - 1
          # make the call
          print("\tmov \trdi, eax")
          print("\tcall " + function_call)
          
      if instruction["codeType"] == "for":
        print("\tnot processed")




# Main routine
def main():

  # Read filename from system arguments
  source = read_source(sys.argv[1])

  # Seperate source code into functions
  unparsed_functions = []
  parenthesis_stack = 0
  inside_function = False
  function = []
  for line in source:
    #print(line," :\t\t", function, inside_function, ":\t\t", parenthesis_stack)
    if "{" in line and inside_function:
      parenthesis_stack = parenthesis_stack + 1;
      function.append(line)
      
    elif "{" in line and not inside_function:
      function.append(line)
      parenthesis_stack = parenthesis_stack + 1
      inside_function = True

    elif "}" in line:
      parenthesis_stack = parenthesis_stack - 1; 
      function.append(line)
      if parenthesis_stack == 0:
        unparsed_functions.append(function)
        function = []
        inside_function = False

    elif inside_function:
      function.append(line)

  #print(unparsed_functions)

  function_list = []
  for unparsed_function in unparsed_functions:
    function = {
        "returnType": "",
        "functionName": "",
        "parameter": [],
        "instruction": []
    }

    head = read_head(unparsed_function[0])
    
    function["returnType"] = head[0]
    function["functionName"] = head[1]

    print(head)

    # iterate over pairs parameter keywords
    i = 2
    while i+2 <= len(head)-1:
      global declaration
      param = {
        "type": head[i],
        "dataName": head[i+1],
        "codeType": "declaration",
        "address": -(declaration*4)
      }
      declaration = declaration + 1
      function["parameter"].append(param)
      i = i + 2
    
    # ignore the first line
    function["instruction"] = read_instruction(1, unparsed_function)["statement"]
    function_list.append(function)
    declaration = 1

  # Print the parsed JSON format of all the functions
  for function in function_list:
    result = json.dumps(function, indent=4)
    print(result)

  # Translate the parsed functions into assembly
  translate(function_list)

main()
