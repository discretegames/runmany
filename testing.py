import sys

print("This is the name of the program:", sys.argv[0])

print("Argument List:", str(sys.argv))

# py -3 .\testing.py foo
# gives Argument List: ['.\\testing.py', 'foo']
