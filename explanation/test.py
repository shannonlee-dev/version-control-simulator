children = {}
parents = ["c000001", "c000002"]
commit_hash = "c000003"

print("Before:", children)

for parent in parents:
    children.setdefault(parent, set()).add(commit_hash)

print("After:", children)
print("c000001의 자식:", children["c000001"])
print("c000002의 자식:", children["c000002"])
