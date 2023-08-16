miller.john 
README.md
3700 Proj 3

In this file, you should briefly describe your high-level approach, any challenges you faced, and an overview of how you tested your code.

High-level approach:
My code is made up of the starter code, which contains the Router class, as well as the Table class I wrote. I added to the Router class to perform base router funtions like dumping the table and forwarding, and most things dealing with the routing table were done in the Table class. This included storing the table, aggregating the table, adding/withdrawing, and finding the best forwarding address for a packet. My approach to this project was to read and fully understand the assignment and specifically all aspects of the router. I know for certain that had I not read and understood everything first this assignment would have taken much longer. Instead, I went one by one implementing things in the order of the tests. 

Challenges:
One thing I had a lot of difficulty with during this project was organizing my code. I solved this by creating lots of methods to improve readablity, but with the one file limit this may not have helped readablity so much. Another challenge I had was with the 6-3 test and reaggregation. I solved this using the simple brute force method of rebuilding the table, and even then I had problems. If I had more time it would have been interesting to pursue other options.

Testing:
I tested my program by working in the order given by the assignment, and passing each level of test one by one. This worked out and I even passed the 5-X tests first try because I had already implemented prefix matching.
