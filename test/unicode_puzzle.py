x = "☠️YOU ARE DEAD"
y = x.encode('ascii', 'ignore').decode('utf-8', 'ignore')
z = "YOU ARE DEAD"
assert y == z, f"this is a mystery: {y}!={z}"
print("This works! {y}=={z}")

x = "YOU ARE DEAD"
for c in x:
    print(ord(c))
y = x.encode('ascii', 'ignore').decode('utf-8', 'ignore')
z = "YOU ARE DEAD"
assert y == z, f"this is a mystery: {y}!={z}"
