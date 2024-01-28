# png_hide
> hide a text into png format image

## install
`pip install git+https://github.com/aidings/png_hide.git`

## example
```python
from png_hide import PNGHide

if __name__ == '__main__':
    h = PNGHide(hide_mode='endian')
    h.encode('b1.jpg', '{x:1, y:2}', 'b1.out.png') # encode dict{x:1, y:2} and save into 'b1.out.png' 

    print(h.decode('b1.out.png'))
```
