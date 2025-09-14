# Glyph-ASCII-Canvas

This program generates ASCII art from images using a different contextual matching approach. Unlike simpler ASCII converters that map pixels directly to characters based on brightness, this algorithm considers the spatial relationships between adjacent blocks for more accurate representations. So it may generate a better result, especially when processing line drawing.

## Usage

```bash
python glyph-ascii-canvas.py [IMAGE_PATH] [OPTIONS]
```

### Options:
| Option              | Description                        | Default              |
| ------------------- | ---------------------------------- | -------------------- |
| `-s`, `--size`      | Per-block size (pixels)            | 10                   |
| `-l`, `--linewidth` | Stroke linewidth of each Character | 0                    |
| `-t`, `--threshold` | Binarization threshold (0-255)     | None                 |
| `-f`, `--font`      | Path to custom font file           | System default       |
| `-c`, `--chars`     | Custom character set               | All ASCII characters |


## How It Works

The algorithm uses following approach to generate ASCII art:

1. **Character Template Generation**:
   - Creates templates for each ASCII character at the specified block size
   - Templates include the character rendered with the selected font
   - Stores templates as grayscale images (6n × 3n pixels)

2. **Image Processing**:
   - Converts input image to grayscale
   - Applies threshold-based binarization (if specified)
   - Pads image to make dimensions divisible by block size

3. **Contextual Block Matching**:
   - For each target block in the image:
     - Creates a "big block" (6n × 3n) containing the target block and its neighbors
     - Compares this big block against all character templates
     - Selects character with the smallest mean squared error (MSE)


## Requirements

- Python 3.6+
- Pillow (PIL Fork)
- NumPy

## Example

![example](./example.svg)

Export above svg file to `example.png` with size of `1200x823`. (Pillow don't support .svg input)

```
> python ./glyph-ascii-canvas.py  -s 24 -l 1 ./example.png
                                                  
       ,__                           ____         
       I \`"**** ~--._      _,.-~~**``  /`|       
       1  }           *-_,-*`          J  j       
        \ }          _,.----._         /  '       
        1 '_      .<"         *-,     Y' J        
         [ ?    ,*               *,   $  )_       
        ,4 Y_,.r                   (_ 1 V' >.     
      -"  .<` /             ,      1 `>-f    '.   
   ,*        wj    Aj      Y'`-     \          '. 
  1,         F    /**,     [**"'    1           -'
    -        [,, 1-,PP+-_  URj~m]   T"-       -'  
      -      Nj_,1[   )  "~4*  _' /N/  `.   -'    
       ^.  x'J'`X*'~~*      `**^4`qd     'J'      
         ~* V1   ^       .     /  J \             
            L \  J `<.__  __,-*\  7"~             
               ',1      ```    {,-                
                 "             `                  
```

```
> python ./glyph-ascii-canvas.py  -s 12 -l 8 ./example.png
                                                                                                    
                                                                                                    
             ,                                                             ____                     
             | `<r``---------...___                            ___..--- ```````y`` ,                
             `   `,                ```--.               _.-- ```              ,'   |                
              ,   `,                     ``-_      _.-"`                      L    j                
              \    j                         `.__.~`                          /    j                
               ,   \                           ``                            y    8'                
               \   f                     _..-- ``````~-._                    (    1                 
                ,  '                _.-"`                ``-_               ,"    ]                 
                t   `             _-`                        `-.            l     j                 
                 ,   `;         _.`                             `-,        -     8'                 
                 \    \        ,'                                 `.       8/    {_                 
                 _,   ,       -`                                    \      1    8' ``-              
              _.-~\   \__.--_/                                       L__    '   /     `-            
            ,-`   {  ,~"`   '                                         j ``-._   '       `.          
         ,-`      "~`      j                           _.             `      ` "          `.        
      _.`                 _j         ,1               y' `.            ,                    `-      
     -`                  @y'        ,' ,              /    `.          `                      `-    
    (                    W1        ,'.~L,            ,  .---*\         8,                       P'  
    `.                   |        ,     `_           j        \         |                     ."    
      -.                 j        j     @@A__        | @____..&;        j-.                 ."      
       `-,               \ ,`,   &)~~;`````Y/`._     w;`qj     ]    ),  j  `.             ."        
         `-              @_j `,  @g-"`     8    `-.__q}~*      l   ,`L_y'    `.         .'          
           `.          _.@qj  q_  A;       ,         `\      _r  _-  @Y'       \      ,'            
             `.       .` Wy````Q>-^*-.__..*`           `-..-W<__-`  8'{         `   ,"              
               -     "   qj     `.                            P``-  { "           ~~'               
                `__.'    Zj      `,                          ,'     ]  ,                            
                  `     / \       `             --           '      j  \                            
                       ,   ,      ]  `._                  ,-<,     8'--&\                           
                       ^-  `,     j    ``-.__        __.~`   `     /                                
                            `.   8j          `````````       8   _/                                 
                              `.  j                          /_.-`                                  
                                `~"                          ``                                     
                                                                                                    
```
