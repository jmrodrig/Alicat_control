class Burner:
    dim_a = 1
    dim_b = 1
    no_holes = 1
    isHole = False
    
    def area(self):
        if self.isHole:
            return math.pi * math.pow(( self.dim_a ) ,2) / 4
        else:
            return self.dim_a * self.dim_b
        

    def D_h(self):
        if self.isHole:
            return self.dim_a
        else:
            return 4 * self.area() / (2 * self.dim_a + 2 + self.dim_b )
