# Glyph-ASCII-Canvas

This program generates ASCII art from images using a sliding window template matching approach. Unlike simpler ASCII converters that map pixels directly to characters based on brightness, this algorithm considers the shape and spatial relationships by comparing image patches against rendered font templates using Mean Squared Error (MSE).

This method typically produces better results for line drawings and structural images by finding the character that structurally "fits" the underlying image patch best.

## Usage

```bash
python glyph-ascii-canvas.py [IMAGE_PATH] [OPTIONS]
```

NOTE: Currently, the image need to have a white background. I am too lazy to add an "invert" option in the script.



### Options

| **Option** | **Long Option** | **Description**                                              | **Default**    |
| ---------- | --------------- | ------------------------------------------------------------ | -------------- |
| `-w`       | `--width`       | Target output width (number of characters). Controls resolution. | `80`           |
| `-r`       | `--char-ratio`  | Character height to width ratio.                             | `2.0`          |
| `-s`       | `--char-scale`  | Font size scaling factor relative to the block size.         | `1.0`          |
| `-l`       | `--linewidth`   | Stroke linewidth used for generating character templates.    | `0`            |
| `-t`       | `--threshold`   | Binarization threshold (0-255). If unset, uses grayscale.    | `None`         |
| `-f`       | `--font`        | Path to a custom `.ttf` font file.                           | System default |
| `-c`       | `--chars`       | Custom ASCII character set to use for matching.              | ASCII (32-126) |
| `-x`       | `--shift-x`     | Shift image position in X direction (pixels) for grid alignment. | `0`            |
| `-y`       | `--shift-y`     | Shift image position in Y direction (pixels) for grid alignment. | `0`            |
| `-a`       | `--auto`        | **Auto Mode**: Try automatic parameter tuning (linewidth, scale, shift) for better quality. | `False`        |

NOTE: Option `-a` will cause the script to take longer to complete. On my laptop (AMD Ryzen 7 6800HS), the time taken for a 60-characters wide image is as follows (statistics using the time command).

```
________________________________________________________
Executed in    3.06 secs    fish           external
   usr time   13.77 secs    0.00 micros   13.77 secs
   sys time    1.40 secs  947.00 micros    1.40 secs
```



## How It Works

The algorithm follows these steps to generate the ASCII output:

1. Dynamic Template Generation:
   - Calculates the precise block size based on the input image width and desired output `--width`.
   - Loads the specified font and renders all candidate characters.
   - Determines a unified window size based on the maximum bounding box of the rendered characters.
2. Canvas Creation & Positioning:
   - Creates a white canvas larger than the target image to accommodate window margins.
   - Pastes the input image (converted to grayscale/binary) onto the canvas.
   - Applies Shift Offsets (`-x`, `-y`) here. This allows fine-tuning the alignment between the pixel grid and the character grid, which significantly reduces alignment artifacts in line drawings.
3. Sliding Window Matching:
   - Uses NumPy strides to create an efficient view of sliding windows over the canvas without duplicating memory.
   - Calculates the Mean Squared Error (MSE) between every image window and every character template.
   - Selects the character with the lowest error for each position.
4. Automatic Tuning (Auto Mode):
   - If `-a` is enabled, the script uses multi-threading to brute-force test combinations of:
     - Linewidths: (0, 1, 2)
     - Scales: (1.0 to 2.4)
     - Shifts: Small pixel offsets in X/Y directions.
   - It automatically selects the result with the lowest total MSE score.



## Requirements

- Python 3.6+
- Pillow (PIL Fork)
- NumPy

## Examples

The following examples use [Maple Mono](https://github.com/subframe7536/maple-font) font.

Original image (`./example/1.png`):

![reimu](./example/1.svg)

Script output:

```
> python ./glyph-ascii-canvas.py -f ./MapleMonoNL-Regular.ttf ./example/1.png -w 60 -a
                                                            
       }^y+=----,,                      ,-=^^^^m+,          
       ]  L           `^=       -+"`          /  }          
        @                 `=.r`               /  [          
        \  @             .-=+^^=-            ~   @          
         @ +         ~"`          `^-        /              
         ]  `      r                  \         ]           
            `@   -`                     @       }^-         
        r`\  @r"~                        8o-   /    @       
     ~"   {^                    --       ]   `^      `=     
  ."           M     c]         ` `@      L            `@   
               }    d""l       / ""`L     ]             .}  
   @          ]        ^}^     [""--=&    ]^,         ./    
     @         . @  @}   ] `^- ]-/   /  },]  `-     ."      
      `-     ~`$--& M    /      L   a -`       L  ./        
        \  ." .[   @                 "^^]       `*          
          9   [@    @,      ,-      [   { @                 
             /.]      "-         ,r`@   }"d                 
                `,        `""""`    j  /                    
                  "=@               O"                      
                                                            

```

You can note the different in lines by the using of different options. For example, changing `-s`.

```
> python ./glyph-ascii-canvas.py -w 60 -s 2.5 -f ./MapleMonoNL-Regular.ttf ./example/1.png
       :                                                    
       |`3C"""""t;^r=~-            -~+=ct""````E`;          
       ]L )            `">~   -c"`            j  {          
        l  [               '^`                (  (          
        ]  [           ~:^""````":~          3   [          
         \ J-       <"             `">       L  J           
         ]  ]L    x'                  `5     t  /           
         -l ]L   /                      \    L  [`">        
      -c" ) x"` /                        \`"z~ {    `x      
   -<'     `   ]      * /^~       L   `       `x    
  c`           #     /]L       J[ -\      \             `~  
  \           ]`    /  `>      {    )     ]             c`  
   `>         ] a  Jw*cff3o-   }cj"""}  * ]`^<       -c`    
     `x       -M \  #'   ]  `"z]b'   { x[o/   \    -c`      
       ^    >' {""\r[>~~<'      `:=c1<^ ]UL    `- <`        
        `>-<  /[   \                x[``]JL      `          
          `   [\    l^      ;'     -[   {-\                 
             {^]L   [ `"z+--  --+^' \  x[ `                 
                 ^-JL               {-<`                    
                   '                `                       
```

Or change `-l`.

```
> python ./glyph-ascii-canvas.py -w 60 -l 4 -f ./MapleMonoNL-Regular.ttf ./example/1.png
                                                            
       /:yz~--,,,                        ,-x"""y>           
          )            `~       ,<"`          d  /          
        L  [               > <`               /  ]          
           }              ,-=zz=,                [          
         \ "         -"            `-        d              
            `      -                  `,                    
          L  \    (                     \       ("-         
        -`]  L<`,                        \>- ` <    l       
     -`    d                     -            "[      >     
   /           j     ,          [  L      )             h   
  ,            $    <``]       < ```)                    d  
   \                   ""\     ]``,,-}     `,          /    
     \           L  [<      b-  L<   /  (L,   -      /      
       L     ,`/,,) $    <      )   <  (       \   /        
        `   /  [   l                 [`"Y        y          
          `   (\    L        ,      (   / \                 
             <      [ `-          <`L   [`h                 
                 -         `````    <  /                    
                  `>L               \`                      
                                                            
```

Larger width give more detailed output.

```
> python ./glyph-ascii-canvas.py -f ./MapleMonoNL-Regular.ttf ./example/1.png -w 120 -a
                                                                                                                        
                                                                                                                        
               } ,--,.                                                                 .,------,.                       
               [   Q   ``"""""""99ypw>=--.                                  ,-~<m^""``        :`   &                    
               $    {.                     `"V@-                   .-<y""``                  d     }                    
               '@    $                           "@-           -g"`                         '@     [                    
                $     }                             `b,    ,g"                               /     L                    
                {.    }                                \-d`                                 {     ]                     
                 Q    {                                   ,,,.                              $     ]                     
                 {.   $                         .-=pP"```      `"k>,                       $      $                     
                  $   L.                    -a"`                    `"@-                   <"     }                     
                  '@   {                 ,F`                            `\>               $      dL                     
                   $    "h=            ~}                                  `\=            }      {                      
                   {     :}          .4                                       {-          \=     }                      
                    L    "?         ~}                                          b         $     db=-                    
                    {     }       .P                                             Q        L     }    \>                 
                 .c" L   `L  ,~sp.}                                               $>,     {    j       `@               
               <"    }    }F`   :}                                                 L ``V@-    .}         {-             
            ~P`      { <"       }                                                  {      `\>./            \-           
         ~F`                   ]             c                   $`b,               L                        {>         
      .d`                     :/           .}{                  ]    {=             {                          {>       
     4`                       $$          :}  L                .}      b             Q                           {@     
   .}                         [}         :[===}>               $ ,==umy^{.           {                             d`   
    {-                       ]          :}     `@              [         {.          {                          .d`     
     `b                      {          }     =--}@.           L~=oo      {.         ]&-                      .d`       
       `@                    {  .-      [.-,,-=smpm}\-         $-<pH"""""``$     >   ]  `@                  .d`         
         `@                  {  } L     $  ]       ]  `\=.     {[  ]       }    .}@  ]    `b.             .d`           
           {=                 Q/  `@    }}`        ]      `"@-. }""       .[   .} `@-}      `L          .4`             
             \-             c"`}    \.  $$         j           `$        ,}   c"  } }         $       .4`               
               b          g"  /}""""`}b-][Q,     ,4              {=,,,-<$} .<"   ]  [          {@    d`                 
                `@      .$    }       L     ````                         `]}>---={  L            Y=-}                   
                  \.   d`    /$        b                                 d`      {  L                                   
                   `@<}     :`{         L                               .}       $  $                                   
                            } '@        {  @            ^P""            $        }   L                                  
                           j   {        /   {=                       ,d $       ]`"@-`@                                 
                          ].~r  L       }     `"@=.              .~p"    L      }                                       
                                 b      L          ``"^p>==smyP"`        }     }                                        
                                  `@    L                                }   c"                                         
                                    `@, $                               j ~F`                                           
                                       `"                               `                                               
                                                                                                                        
                                                                                                                        

```

### Other examples:

#### 2

![shapes](./example/2.png)

```
> python ./glyph-ascii-canvas.py -w 60 -s 2.5 -f ./MapleMonoNL-Regular.ttf ./example/2.png
                                                               
                                                               
                                                               
             <````````````QMC            -~~~-                 
           *(           -Z[]C         <C`    ``b~              
         v#mmmmmmmmmmmm<{  ]C       yC          ]5             
         ]C            [   ]C       (             l            
         ]C            [   ]C      JL             )            
         ]C            [   ]C       \             [            
         ]C            [   ]C       ]>          -/             
         ]C            [  <{          `zw-   -<^`              
         ]C            [*C               ````                  
         ]ttttttttttttt"        >                              
                                {3~                            
                               7  }w~~~~~                      
                          *m^""`      ]/                       
                           `^>       4(                        
                              )      \                         
                              ( *C`tmw\                        
                              P"      `                        
                                                               
                                                               
                                                               
```

#### 3

![qwq](./example/3.png)

```
> python ./glyph-ascii-canvas.py -f ./MapleMonoNL-Regular.ttf ./example/3.png -a
                                                                                
                                    .                                           
                              .~aI---,,  ,g^"`""k>-                             
                          ,<" <m=.   ,}"            `@,                         
                       ~"        ,`"=  ``=             `@.                      
                    -/                                    \                     
                  <"                  ,                    `@                   
                c"                    }                      {-                 
              .$                     /               ` `@     `h                
             c}   `                 d     -    .                {@              
            4`   `  } t   .        d       \   `-                `h             
           $    `        .}       d         `h   \                 $            
          $              [       /            `t, `@                $           
         /              /    [ -"                "@ {@              {Q          
        d}           : /    /~"                  -=}""VW/\           {L         
        $            }:~$}"{}@-               -F            .        '$         
       .}         ] .      "    \                           ]         $         
       ]L       .~{ ]                                         .,      $L        
       }      ,`  { {                          c'`">,        @  `h    $L        
       $      }   } $     ,    ,              [  ..- `       L   {@   $L        
       }      L   } $       .`t                 $$$8L        L   j    $L        
       $      {-  { {}     N$${L                $}"`      , ]   d}    $         
       $       {@. Q \L     }y}        :              ~"    $^M}      $         
       {L        ``{@ [L~-, `                       ~"     $          $         
        {.          {@{ L    "-          ,-=       d`    .$           $@        
         $           {@\ \     `=    .'    }       }    d}            {$        
          $.            `@`     {    `h,  4        }  4}               $L       
           {@             `t-   $       ``        ,}N"            @     ""      
            `Q.               "@-.           .-g$`    `=        .o>}>           
              {@  .               `"VkmwmpH${}     ]L    \=      -   ``         
               {L ]         .'  .     `=. ,d"     ~}       {@    `              
                $.   `    -"    !       .       ,N`                             
              @$`     ` ~[       "-  ,<P` `>-~a"                                
                                                                                
                                                                                

```

#### 4

![pig](./example/4.png)

```
> python ./glyph-ascii-canvas.py -f ./MapleMonoNL-Regular.ttf ./example/4.png -a
                                                                                
                           .,                                                   
                  ." \   ./  `.                      ,-     .d``@               
                 :    \ :     {                    ~`  \   /    {               
                d      W       L                 .[    { ~`     ]               
      ,  ,---  d                  ````""""""^^  .[     '/        L ""^=.        
     d"`      ``                                "               -^`  `  `-      
    d ...        {`                                            /          @     
    [     `                                                               }     
    `,                                                         \      "-  }     
      `">==="      c>        -^^^^^>>=--,..    \                `=     .}[      
           {    .d  {      <`               ``  \      ~"@         `Y9``  `     
            \,-/     `>-="                       \,.,g`   L      ~^`            
                                                           `"""`                
                                                                                
                                                                                
```

#### 5

![bear](./example/5.png)

```
> python ./glyph-ascii-canvas.py -f ./MapleMonoNL-Regular.ttf ./example/5.png -a
                                                    ..                          
                                      .-=^^"""`  c     \                        
                       .-^"`"^>- .^`                    L                       
              <`   `.'                                 d                        
             {                                        `=                        
              ^                                         \                       
                                                         `.                     
                                           :>             {                     
              ]          `                                .    ,~==-            
              {                  ~^P`                     ':"`       \          
               @                   [                                  }         
           -=^""L                  }\   ~                             `         
        -"                     ```}   {                             .`          
       :                          L   /                           ./            
       [                          `^<"                           :              
       \                                                         {              
        -                                                        {     -^"@     
         \                                                        L ~`  -"      
           \                                                       \ -^`        
            `                                                       `@          
             L                          .,-====-,                     \         
             [                   ,='``              ``^=-              [        
             L          .---<"`                            `^-,..,   ,/         
            .          .`                                        ^^"            
            {         c                                                         
             "=.  .~'                                                           

```
