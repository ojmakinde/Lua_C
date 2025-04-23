a = 0
b = 1
count = 0
print("Enter max fib iteration")
max = io.read("*n")
while count <= max do
    print(a)
    count = count + 1
    temp = a + b
    a = b
    b = temp
end