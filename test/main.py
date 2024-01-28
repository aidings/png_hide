from png_hide import PNGHide

if __name__ == '__main__':
    h = PNGHide(hide_mode='endian')
    h.encode('b1.jpg', '{x:1, y:2}', 'b1.out.png')

    print(h.decode('b1.out.png'))