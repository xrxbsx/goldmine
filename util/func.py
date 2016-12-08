"""General utility functions."""
def bdel(s, r): return (s[len(r):] if s.startswith(r) else s)
