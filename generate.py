from random import randint

if __name__ == '__main__':
    w = 1000
    h = 1000
    min_val = -1000
    max_val = 2000
    for i in range(h):
        for j in range(w-1):
            if randint(0,10) < 8:
                print(randint(min_val, max_val), end=',')
            else:
                print(1, end=',')
        print(randint(min_val, max_val))
