$fn = 40;

// uncomment, when using via OpenSCAD
// BasePlate(inner_size=82, margin=0);

module BasePlate(bt_thickness=0.3, total_thickness=1.1, inner_size=60, margin=5, outer_brim=2, hole_r=1.5, hole_margin=10, outer_radius=5){
    
    width = inner_size + 2*margin + 2*outer_brim;
    length = inner_size + 2*margin + 2*outer_brim+hole_margin;
    translate([length/2-margin-outer_brim, width/2-margin-outer_brim, 0]){
        color(c="white"){
            difference(){
                union(){
                    // Rounded rect with lip
                    difference(){
                        RoundedRect(
                            length,                     // length
                            width,                      // width
                            total_thickness,            // thickness
                            outer_radius,               // R
                            0, 0, 0);                   // x,y,z
                        RoundedRect(
                            length-outer_brim/2,        // length
                            width-outer_brim/2,         // width
                            total_thickness,            // thickness
                            outer_radius-outer_brim/4,    // R
                            0, 0, bt_thickness);        // x,y,z        
                    }
                    // hole outer
                    translate([length/2-hole_margin/2,0,0]){                        
                        cylinder(h=total_thickness, r=hole_r*2);
                    }
                }
                // hole inner
                translate([length/2-hole_margin/2,0,0]){
                    cylinder(h=total_thickness, r=hole_r);
                }
            }
        }
    }
}

module RoundedRect(length, width, height, radius, x=0, y=0, z=0){
    offsetX = length/2.0 - radius;
    offsetY = width/2.0 - radius;
    hull(){
        translate([-offsetX+x,-offsetY+y,z]){
            cylinder(h = height, r = radius);
        }
        translate([-offsetX+x, offsetY+y,z]){
            cylinder(h = height, r = radius);
        }
        translate([ offsetX+x, offsetY+y,z]){
            cylinder(h = height, r = radius);
        }
        translate([ offsetX+x,-offsetY+y,z]){
            cylinder(h = height, r = radius);
        }    
    }
}