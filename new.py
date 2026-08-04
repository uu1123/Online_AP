class Student():
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def showinfo(self):
        print("Name: ", self.name, "Age: ", self.age)

stu1 = Student("qq",44)
stu2 = Student("UU", 22)
print(stu1 is stu2)
print(id(stu1))
print(id(stu2))