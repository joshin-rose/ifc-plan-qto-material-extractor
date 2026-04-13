## Create a new user for the MySQL

'''
CREATE USER IF NOT EXISTS 'architect'@'localhost' IDENTIFIED BY 'ap@2101';
GRANT ALL PRIVILEGES ON *.* TO 'architect'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
'''

## Create Database

CREATE DATABASE arch_db;
USE arch_db;

## Define Schema for Tables

# sor_data

CREATE TABLE sor_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sor_code VARCHAR(50) UNIQUE,
    state_name VARCHAR(100),
    year INT,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO sor_data (sor_code, state_name, year, name)
VALUES ('TN_SOR_2025', 'Tamil Nadu', 2025, 'TamilNadu_SOR_2025');

# sor_labour_category

CREATE TABLE sor_labour_category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sor_code VARCHAR(50),
    category_code VARCHAR(10),
    category_name VARCHAR(100),

    UNIQUE (sor_code, category_code),

    FOREIGN KEY (sor_code) REFERENCES sor_data(sor_code)
);

INSERT INTO sor_labour_category (sor_code, category_code, category_name) VALUES
('TN_SOR_2025','I','Highly Skilled Category'),
('TN_SOR_2025','II','Skilled Category'),
('TN_SOR_2025','III','Semi Skilled Category'),
('TN_SOR_2025','IV','Unskilled Category');

# sor_labour_data

CREATE TABLE sor_labour_data (
    id INT AUTO_INCREMENT PRIMARY KEY,

    sor_code VARCHAR(50),
    category_code VARCHAR(10),

    unique_code VARCHAR(20) UNIQUE,
    description TEXT,
    unit VARCHAR(20),
    base_rate DECIMAL(10,2),

    FOREIGN KEY (sor_code) REFERENCES sor_data(sor_code),
    FOREIGN KEY (sor_code, category_code)
        REFERENCES sor_labour_category(sor_code, category_code)
);


INSERT INTO sor_labour_data (sor_code, category_code, unique_code, description, unit, base_rate) VALUES
('TN_SOR_2025','I','L-0001','Technical Assistant Grade-I (B.E Passed)','Day',1430.00),
('TN_SOR_2025','I','L-0002','Technical Assistant Grade-II (Diploma in Engg Passed / B.E Failed / Degree in Geology for Ground Water Works)','Day',1289.00),
('TN_SOR_2025','I','L-0003','Technical Assistant Grade-III (Diploma in Engg Failed / ITI Civil Passed)','Day',1089.00),
('TN_SOR_2025','I','L-0004','Cinema Operator (ITI Passed)','Day',897.00),
('TN_SOR_2025','I','L-0009','Computer Operator Grade-I','Day',1430.00),
('TN_SOR_2025','I','L-0010','Computer Operator Grade-II','Day',1289.00),
('TN_SOR_2025','I','L-0013','Wireman Grade-I / Electrician Grade-I','Day',971.00),
('TN_SOR_2025','I','L-0130','Architect Assistant Grade-I (B.Arch Passed)','Day',1430.00),
('TN_SOR_2025','I','L-0131','Conservation Architect Assistant Grade-I (B.Arch Passed)','Day',1430.00);

INSERT INTO sor_labour_data (sor_code, category_code, unique_code, description, unit, base_rate) VALUES
('TN_SOR_2025','II','L-0014','Blacksmith-I Class','Day',904.00),
('TN_SOR_2025','II','L-0016','Carpenter-I Class','Day',1148.00),
('TN_SOR_2025','II','L-0017','Cleaner-First Grade','Day',609.00),
('TN_SOR_2025','II','L-0018','Fitter-I Class','Day',1036.00),
('TN_SOR_2025','II','L-0019','Fitter (Pipe Laying / Bar Bending)-I Class','Day',1018.00),
('TN_SOR_2025','II','L-0020','Floor Polisher','Day',904.00),
('TN_SOR_2025','II','L-0021','Hammer Mazdoor','Day',726.00),
('TN_SOR_2025','II','L-0023','Driver (Light Duty)','Day',904.00),
('TN_SOR_2025','II','L-0024','Driver (Heavy Duty)','Day',965.00),
('TN_SOR_2025','II','L-0025','Maistry Road Inspector & Work Inspector','Day',870.90),
('TN_SOR_2025','II','L-0026','Maistry Road Inspector & Work Inspector (Degree Holder)','Day',965.00),
('TN_SOR_2025','II','L-0027','Skilled Mason Class-I for Heritage Work','Day',1657.00),
('TN_SOR_2025','II','L-0028','Skilled Mason Class-II for Heritage Work','Day',1449.00),
('TN_SOR_2025','II','L-0029','Mason for Brick Work-I Class','Day',1174.00),
('TN_SOR_2025','II','L-0030','Skilled Sthapathy Brick Mason for Heritage Work','Day',2072.00),
('TN_SOR_2025','II','L-0031','Mason for Stone Work-I Class','Day',1174.00),
('TN_SOR_2025','II','L-0032','Skilled Sthapathy Stone Mason for Heritage Work','Day',2072.00),
('TN_SOR_2025','II','L-0033','Mechanic-I Class','Day',904.00),
('TN_SOR_2025','II','L-0036','Painter / Varnisher-I Class','Day',937.00),
('TN_SOR_2025','II','L-0037','Pile Driver','Day',832.00),
('TN_SOR_2025','II','L-0038','Plumber-I Class','Day',1018.00),
('TN_SOR_2025','II','L-0039','Sawyer','Day',832.00),
('TN_SOR_2025','II','L-0040','Smith-I Class','Day',900.00),
('TN_SOR_2025','II','L-0041','Stone Cutter-I Class','Day',900.00),
('TN_SOR_2025','II','L-0042','Syrang-I Class','Day',900.00),
('TN_SOR_2025','II','L-0043','Tinker-I Class','Day',726.00),
('TN_SOR_2025','II','L-0044','Turner-I Class','Day',832.00),
('TN_SOR_2025','II','L-0045','Time Keeper-I Class','Day',900.00),
('TN_SOR_2025','II','L-0046','Welder / Bracer-I Class','Day',900.00),
('TN_SOR_2025','II','L-0050','Wodder','Day',757.00),
('TN_SOR_2025','II','L-0051','Compressor Operator','Day',796.00),
('TN_SOR_2025','II','L-0053','Stone & Crusher Operator','Day',796.00),
('TN_SOR_2025','II','L-0054','Wireman Grade-II / Electrician Grade-II','Day',965.00),
('TN_SOR_2025','II','L-0055','Lift Operator','Day',870.00),
('TN_SOR_2025','II','L-0056','Laboratory Attendant','Day',648.00),
('TN_SOR_2025','II','L-0057','Sound Service Operator','Day',726.00),
('TN_SOR_2025','II','L-0058','Electrical Maistry','Day',1113.00);

INSERT INTO sor_labour_data (sor_code, category_code, unique_code, description, unit, base_rate) VALUES
('TN_SOR_2025','III','L-0059','Axe Mazdoor','Day',714.00),
('TN_SOR_2025','III','L-0060','Blacksmith-II Class','Day',867.00),
('TN_SOR_2025','III','L-0061','Bullocks Pair with Driver (with Bandy)','Day',1416.00),
('TN_SOR_2025','III','L-0062','Bullocks Single with Driver (with Bandy)','Day',1018.00),
('TN_SOR_2025','III','L-0063','Carpenter-II Class','Day',1096.00),
('TN_SOR_2025','III','L-0065','Cleaner-Second Grade','Day',603.00),
('TN_SOR_2025','III','L-0067','Fitter-II Class','Day',1006.00),
('TN_SOR_2025','III','L-0068','Fitter (Pipe Laying / Bar Bending)-II Class','Day',986.00),
('TN_SOR_2025','III','L-0069','Gardener','Day',714.00),
('TN_SOR_2025','III','L-0070','Jumper Mazdoor','Day',714.00),
('TN_SOR_2025','III','L-0071','Mason for Brick Work-II Class','Day',1096.00),
('TN_SOR_2025','III','L-0072','Mason for Stone Work-II Class','Day',1096.00),
('TN_SOR_2025','III','L-0073','Mazdoor Category-I','Day',766.00),
('TN_SOR_2025','III','L-0074','Head Mazdoor','Day',792.00),
('TN_SOR_2025','III','L-0075','Mechanic-II Class','Day',867.00),
('TN_SOR_2025','III','L-0077','Painter / Varnisher-II Class','Day',908.00),
('TN_SOR_2025','III','L-0078','Plumber-II Class','Day',986.00),
('TN_SOR_2025','III','L-0079','Pump Driver','Day',792.00),
('TN_SOR_2025','III','L-0080','Smith-II Class','Day',867.00),
('TN_SOR_2025','III','L-0081','Stone Cutter-II Class','Day',867.00),
('TN_SOR_2025','III','L-0082','Syrang-II Class','Day',867.00),
('TN_SOR_2025','III','L-0083','Thatcher','Day',757.00),
('TN_SOR_2025','III','L-0084','Tinker-II Class','Day',714.00),
('TN_SOR_2025','III','L-0085','Turner-II Class','Day',792.00),
('TN_SOR_2025','III','L-0086','Time Keeper-II Class','Day',867.00),
('TN_SOR_2025','III','L-0087','Welder / Bracer-II Class','Day',867.00),
('TN_SOR_2025','III','L-0091','Mazdoor employed for Pitting Trenching Sampling & Drilling works','Day',767.00),
('TN_SOR_2025','III','L-0092','Mazdoor employed for Geophysical investigation works','Day',767.00),
('TN_SOR_2025','III','L-0093','Head Mazdoor to supervise exploratory works','Day',808.00),
('TN_SOR_2025','III','L-0094','Mixer Operator (including concrete mixer)','Day',832.00),
('TN_SOR_2025','III','L-0095','Mixer Driver','Day',792.00),
('TN_SOR_2025','III','L-0096','Heavy Mazdoor','Day',832.00),
('TN_SOR_2025','III','L-0097','Electrical Helper','Day',757.00);

INSERT INTO sor_labour_data (sor_code, category_code, unique_code, description, unit, base_rate) VALUES
('TN_SOR_2025','IV','L-0098','Mazdoor Category-II','Day',628.00);


# Material Category Table

CREATE TABLE sor_material_category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sor_code VARCHAR(50),
    category_code VARCHAR(10),
    category_name VARCHAR(255),

    UNIQUE (sor_code, category_code),

    FOREIGN KEY (sor_code) REFERENCES sor_data(sor_code)
);

INSERT INTO sor_material_category (sor_code, category_code, category_name) VALUES
('TN_SOR_2025','GEN','General Materials'),
('TN_SOR_2025','A','Bricks and Tile Products'),
('TN_SOR_2025','B','Stone and Road Materials'),
('TN_SOR_2025','C','Lime'),
('TN_SOR_2025','D','Timber and Roofing Materials'),
('TN_SOR_2025','E','Metal and Iron Items'),
('TN_SOR_2025','F','Heritage Conservation Materials'),
('TN_SOR_2025','ECBC','Energy Conservation Building Code Materials');

# Material Subcategory Table
CREATE TABLE sor_material_subcategory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sor_code VARCHAR(50),
    category_code VARCHAR(10),
    subcategory_name VARCHAR(255),

    FOREIGN KEY (sor_code, category_code)
        REFERENCES sor_material_category(sor_code, category_code)
);

INSERT INTO sor_material_subcategory (sor_code, category_code, subcategory_name) VALUES
('TN_SOR_2025','A','Second Class Table Moulded Chamber Burnt Bricks'),
('TN_SOR_2025','A','Second Class Ground Moulded Chamber Burnt Bricks'),
('TN_SOR_2025','A','Third Class Country Brick Kiln Burnt'),
('TN_SOR_2025','A','Fly Ash Bricks'),
('TN_SOR_2025','A','Specially Moulded Country Brick for Well Steining'),
('TN_SOR_2025','A','Wire Cut Bricks for Heritage Works'),
('TN_SOR_2025','A','Flat Tiles'),
('TN_SOR_2025','A','Brick Jelly'),
('TN_SOR_2025','A','Pressed Tiles'),
('TN_SOR_2025','A','Pan Tiles'),
('TN_SOR_2025','A','Best Mangalore Tiles'),
('TN_SOR_2025','A','Mosaic Flooring Tiles (Grey)'),
('TN_SOR_2025','A','Mosaic (other Colour)'),
('TN_SOR_2025','A','Attangudi Tiles for Heritage Works');

INSERT INTO sor_material_subcategory (sor_code, category_code, subcategory_name) VALUES
('TN_SOR_2025','B','Hard Broken Granite Stone Jelly (I.S.S.) Machine crushed / Hand broken'),
('TN_SOR_2025','B','Quartz Metal');

INSERT INTO sor_material_subcategory (sor_code, category_code, subcategory_name) VALUES
('TN_SOR_2025','D','Teak Wood Reepers'),
('TN_SOR_2025','D','Country Wood Scantlings'),
('TN_SOR_2025','D','Country Wood Planks'),
('TN_SOR_2025','D','Country Wood Reepers'),
('TN_SOR_2025','D','Casurina Poles'),
('TN_SOR_2025','D','Eucalyptus Poles');

INSERT INTO sor_material_subcategory (sor_code, category_code, subcategory_name) VALUES
('TN_SOR_2025','F','Seasoned Teakwood Scantlings and Planks for Heritage Works'),
('TN_SOR_2025','F','FAT LIME Putty with following Specifications - CaO content more than 90% and lime concentration 60-62% by weight with infinite shelf life when stored under water');

INSERT INTO sor_material_subcategory (sor_code, category_code, subcategory_name) VALUES
('TN_SOR_2025','ECBC','Specification for Burnt Clay Hollow Bricks for Walls'),
('TN_SOR_2025','ECBC','Autoclaved Cellular Aerated Concrete Panel');

ALTER TABLE sor_material_subcategory
ADD UNIQUE (sor_code, category_code, subcategory_name);

# Material Data Table
CREATE TABLE sor_material_data (
    id INT AUTO_INCREMENT PRIMARY KEY,

    sor_code VARCHAR(50),
    category_code VARCHAR(10),
    subcategory_name VARCHAR(255),

    unique_code VARCHAR(20) UNIQUE,
    description TEXT,
    unit VARCHAR(50),
    base_rate DECIMAL(12,2),

    FOREIGN KEY (sor_code) 
        REFERENCES sor_data(sor_code),

    FOREIGN KEY (sor_code, category_code)
        REFERENCES sor_material_category(sor_code, category_code),

    FOREIGN KEY (sor_code, category_code, subcategory_name)
        REFERENCES sor_material_subcategory(sor_code, category_code, subcategory_name)
);

INSERT INTO sor_material_data
(sor_code, category_code, subcategory_name, unique_code, description, unit, base_rate)
VALUES
('TN_SOR_2025','GEN',NULL,'M-0001','Cement','MT',5602.50),
('TN_SOR_2025','GEN',NULL,'M-0002','Steel','MT',55665.00);

INSERT INTO sor_material_data
(sor_code,category_code,subcategory_name,unique_code,description,unit,base_rate)
VALUES
('TN_SOR_2025','A','Second Class Table Moulded Chamber Burnt Bricks','M-0003','9 x 4 1/2 x 3','1000 Nos.',7887.00),
('TN_SOR_2025','A','Second Class Table Moulded Chamber Burnt Bricks','M-0004','9 x 4 3/8 x 2 3/4','1000 Nos.',7585.00),

('TN_SOR_2025','A','Second Class Ground Moulded Chamber Burnt Bricks','M-0005','9 x 4 1/2 x 3','1000 Nos.',6795.00),
('TN_SOR_2025','A','Second Class Ground Moulded Chamber Burnt Bricks','M-0006','9 x 4 3/8 x 2 3/4','1000 Nos.',6595.00),

('TN_SOR_2025','A','Third Class Country Brick Kiln Burnt','M-0007','8 3/4 x 4 1/4 x 2 3/4','1000 Nos.',5709.00),
('TN_SOR_2025','A','Third Class Country Brick Kiln Burnt','M-0008','8 3/4 x 4 1/4 x 2 1/4','1000 Nos.',4489.00),
('TN_SOR_2025','A','Third Class Country Brick Kiln Burnt','M-0009','8 3/4 x 4 1/4 x 2','1000 Nos.',4299.00),

('TN_SOR_2025','A','Fly Ash Bricks','M-0010','230 x 110 x 70mm','1000 Nos.',6595.00),
('TN_SOR_2025','A','Fly Ash Bricks','M-0011','230 x 110 x 75mm','1000 Nos.',6795.00),

('TN_SOR_2025','A','Specially Moulded Country Brick for Well Steining','M-0012','8 3/4 x 4 1/4 x 2','1000 Nos.',2526.00),
('TN_SOR_2025','A','Specially Moulded Country Brick for Well Steining','M-0013','Perforated Bricks 19 x 9 x 9cm','1000 Nos.',3854.00),
('TN_SOR_2025','A','Specially Moulded Country Brick for Well Steining','M-0014','Terrace Bricks 15 x 7.5 x 2.5cm','1000 Nos.',989.00),
('TN_SOR_2025','A','Specially Moulded Country Brick for Well Steining','M-0015','Special Bricks 8 x 4 x 2 for Heritage Works','1000 Nos.',13365.00),
('TN_SOR_2025','A','Specially Moulded Country Brick for Well Steining','M-0016','Terrace Bricks 6 x 3 x 1 for Heritage Works','1000 Nos.',10020.00),

('TN_SOR_2025','A','Wire Cut Bricks for Heritage Works','M-0017','Size 9 x 4 x 3','1000 Nos.',13365.00),
('TN_SOR_2025','A','Wire Cut Bricks for Heritage Works','M-0018','Size 9 x 4 x 2','1000 Nos.',11140.00),
('TN_SOR_2025','A','Wire Cut Bricks for Heritage Works','M-0019','Size 9 x 6.5 x 2','1000 Nos.',16705.00),

('TN_SOR_2025','A','Flat Tiles','M-0020','15cm x 15cm x 12mm','1000 Nos.',8087.00),
('TN_SOR_2025','A','Flat Tiles','M-0021','15cm x 15cm x 20mm','1000 Nos.',9604.00),

('TN_SOR_2025','A','Brick Jelly','M-0022','40mm size','cum.',705.00),
('TN_SOR_2025','A','Brick Jelly','M-0023','20mm size','cum.',786.00),

('TN_SOR_2025','A','Pressed Tiles','M-0024','20 x 20 x 2cm','1000 Nos.',11356.00),
('TN_SOR_2025','A','Pressed Tiles','M-0025','23 x 23 x 2cm','1000 Nos.',16106.00),

('TN_SOR_2025','A','Pan Tiles','M-0026','23cm x 8cm x 1.7cm','1000 Nos.',441.35),
('TN_SOR_2025','A','Pan Tiles','M-0027','16.5cm x 8cm x 1.7cm','1000 Nos.',363.30),

('TN_SOR_2025','A','Best Mangalore Tiles','M-0028','I Class A','1000 Nos.',10594.00),
('TN_SOR_2025','A','Best Mangalore Tiles','M-0029','Class AA','1000 Nos.',10807.00),
('TN_SOR_2025','A','Best Mangalore Tiles','M-0030','Best Mangalore Ridge Tiles','1000 Nos.',31007.00),
('TN_SOR_2025','A','Best Mangalore Tiles','M-0031','Best Mangalore Ceiling Tiles','1000 Nos.',6514.00),
('TN_SOR_2025','A','Best Mangalore Tiles','M-0032','Best Mangalore Glass Roofing Tiles','Each',304.00),
('TN_SOR_2025','A','Best Mangalore Tiles','M-0033','Best Mangalore Ventilating Tiles (Single)','Each',45.45),
('TN_SOR_2025','A','Best Mangalore Tiles','M-0034','Best Mangalore Ventilating Tiles (Double)','Each',57.55),

('TN_SOR_2025','A','Mosaic Flooring Tiles (Grey)','M-0035','Mosaic (Grey) Tile 25 x 25 x 2cm','1000 Nos.',11907.00),
('TN_SOR_2025','A','Mosaic Flooring Tiles (Grey)','M-0036','Mosaic (Grey) Tile 20 x 20 x 2cm','1000 Nos.',7605.00),

('TN_SOR_2025','A','Mosaic (other Colour)','M-0037','Mosaic (other colour) Tile 25x25x2cm','1000 Nos.',16432.00),
('TN_SOR_2025','A','Mosaic (other Colour)','M-0038','Mosaic (other colour) Tile 20x20x2cm','1000 Nos.',9696.00),
('TN_SOR_2025','A','Mosaic (other Colour)','M-0039','Mosaic (Green) Tile 20 x 20 x 2cm','1000 Nos.',11907.00),
('TN_SOR_2025','A','Mosaic (other Colour)','M-0040','Mosaic (Green) Tile 25 x 25 x 2cm','1000 Nos.',18674.00),
('TN_SOR_2025','A','Mosaic (other Colour)','M-0041','Mosaic Chequered Tile Grey Colour Size 25 x 25 x 2 cm','1000 Nos.',14948.00),

('TN_SOR_2025','A','Attangudi Tiles for Heritage Works','M-0042','Size 8 x 8 x 3/4','Each',26.95),
('TN_SOR_2025','A','Attangudi Tiles for Heritage Works','M-0043','Size 10 x 10 x 3/4','Each',32.70),
('TN_SOR_2025','A','Attangudi Tiles for Heritage Works','M-0044','Size 12 x 12 x 3/4','Each',50.00);

INSERT INTO sor_material_data
(sor_code,category_code,subcategory_name,unique_code,description,unit,base_rate)
VALUES
('TN_SOR_2025','B',NULL,'M-0045','Rough Stone for masonry works (Hard Granite)','cum.',449.40),
('TN_SOR_2025','B',NULL,'M-0048','Cut Stone Pillar of size 0.15 x 0.15 x 2.10m','Each',165.60),
('TN_SOR_2025','B',NULL,'M-0050','From boulders without blasting for masonry','cum.',147.45),
('TN_SOR_2025','B',NULL,'M-0051','Course Rubble Stone for masonry works','cum.',358.50),
('TN_SOR_2025','B',NULL,'M-0052','Course Rubble Stone for Arch works','cum.',388.80),
('TN_SOR_2025','B',NULL,'M-0058','Ashlar Arch Stone Fully Dressed to size all faces','cum.',4893.00),
('TN_SOR_2025','B',NULL,'M-0059','Flooring Stone SS Size (Not less than 10cm thick)','sqm.',356.50),
('TN_SOR_2025','B',NULL,'M-0064','Bond Stones','cum.',648.40),

('TN_SOR_2025','B','Hard Broken Granite Stone Jelly (I.S.S.) Machine crushed / Hand broken','M-0082','HBGS Jelly 90mm size','cum.',583.20),
('TN_SOR_2025','B','Hard Broken Granite Stone Jelly (I.S.S.) Machine crushed / Hand broken','M-0083','HBGS Jelly 80mm size','cum.',653.10),
('TN_SOR_2025','B','Hard Broken Granite Stone Jelly (I.S.S.) Machine crushed / Hand broken','M-0084','HBGS Jelly 63mm size','cum.',754.00),
('TN_SOR_2025','B','Hard Broken Granite Stone Jelly (I.S.S.) Machine crushed / Hand broken','M-0085','HBGS Jelly 50mm size','cum.',875.40),
('TN_SOR_2025','B','Hard Broken Granite Stone Jelly (I.S.S.) Machine crushed / Hand broken','M-0086','HBGS Jelly 40mm size','cum.',1362.90),
('TN_SOR_2025','B','Hard Broken Granite Stone Jelly (I.S.S.) Machine crushed / Hand broken','M-0087','HBGS Jelly 25mm size','cum.',1170.50),
('TN_SOR_2025','B','Hard Broken Granite Stone Jelly (I.S.S.) Machine crushed / Hand broken','M-0088','HBGS Jelly 20mm size','cum.',1897.40),
('TN_SOR_2025','B','Hard Broken Granite Stone Jelly (I.S.S.) Machine crushed / Hand broken','M-0089','HBGS Jelly 12mm size','cum.',1760.50),
('TN_SOR_2025','B','Hard Broken Granite Stone Jelly (I.S.S.) Machine crushed / Hand broken','M-0090','HBGS Jelly 10mm size','cum.',1294.40),
('TN_SOR_2025','B','Hard Broken Granite Stone Jelly (I.S.S.) Machine crushed / Hand broken','M-0091','HBGS Jelly 6mm size','cum.',875.40),
('TN_SOR_2025','B','Hard Broken Granite Stone Jelly (I.S.S.) Machine crushed / Hand broken','M-0092','HBGS Jelly 3mm size','cum.',787.50),

('TN_SOR_2025','B','Quartz Metal','M-0107','Quartz Metal 50mm','cum.',97.75),
('TN_SOR_2025','B','Quartz Metal','M-0108','Quartz Metal 40mm','cum.',98.75),

('TN_SOR_2025','B',NULL,'M-0115','Laterite 40 to 75mm size','cum.',97.75),
('TN_SOR_2025','B',NULL,'M-0116','Kankar 40 to 75mm size','cum.',97.75),
('TN_SOR_2025','B',NULL,'M-0117','Soling Stones un-blasted 15cm cube','cum.',114.10),
('TN_SOR_2025','B',NULL,'M-0118','Soling Stones blasted 15cm cube','cum.',185.80),
('TN_SOR_2025','B',NULL,'M-0119','Gravel','cum.',222.70),
('TN_SOR_2025','B',NULL,'M-0120','Well Gravel','cum.',166.50),
('TN_SOR_2025','B',NULL,'M-0121','Screened Kankar Gravel','cum.',121.90),
('TN_SOR_2025','B',NULL,'M-0122','Quarry Rubbish','cum.',96.65),
('TN_SOR_2025','B',NULL,'M-0124','Pond Ash (wet / dry)','cum.',95.65),
('TN_SOR_2025','B',NULL,'M-0125','Crushed Stone Sand (Commercially called M-Sand)','cum.',1578.80),
('TN_SOR_2025','B',NULL,'M-0126','Plastering Sand (P-Sand)','cum.',1584.70),
('TN_SOR_2025','B',NULL,'M-0127','Sand for Mortar','cum.',0.00),
('TN_SOR_2025','B',NULL,'M-0128','Sand for Filling','cum.',0.00),
('TN_SOR_2025','B',NULL,'M-0129','Clay for Puddle & Masonry','cum.',37.35),
('TN_SOR_2025','B',NULL,'M-0130','Cuddapah Slab 50mm Thick','sqm.',425.00),
('TN_SOR_2025','B',NULL,'M-0131','Cuddapah Slab 38 / 40mm Thick','sqm.',408.00),
('TN_SOR_2025','B',NULL,'M-0132','Cuddapah Slab 20 / 30mm Thick','sqm.',376.70);

INSERT INTO sor_material_data
(sor_code,category_code,subcategory_name,unique_code,description,unit,base_rate)
VALUES
('TN_SOR_2025','C',NULL,'M-0133','Shell Lime (Slaked & Screened)','cum.',1348.00),
('TN_SOR_2025','C',NULL,'M-0134','Freshly Slaked & Screened Burnt Lime Stone','cum.',993.00),
('TN_SOR_2025','C',NULL,'M-0135','Stone Lime or Lime Metal','cum.',85.60),
('TN_SOR_2025','C',NULL,'M-0136','Unslaked Freshly Burnt Lime (CaO not less than 75%) for use in Heritage Construction Works','cum.',10345.00),
('TN_SOR_2025','C',NULL,'M-0137','Freshly Slaked and Screened Lime (CaO not less than 85%) for Theervai Plastering in Heritage Works','cum.',15500.00);

INSERT INTO sor_material_data
(sor_code,category_code,subcategory_name,unique_code,description,unit,base_rate)
VALUES
('TN_SOR_2025','D',NULL,'M-0138','TW Scantlings (over 3m for joist and rafters) - Malabar','cum.',116600.00),
('TN_SOR_2025','D',NULL,'M-0139','TW Scantlings (for tiebeams & principal rafters) - Malabar','cum.',114700.00),
('TN_SOR_2025','D',NULL,'M-0140','TW Scantlings (over 2m & below 3m in length) - Malabar','cum.',111600.00),
('TN_SOR_2025','D',NULL,'M-0141','TW Scantling (below 2m in length) - Malabar','cum.',99400.00),
('TN_SOR_2025','D',NULL,'M-0142','TW Planks (over 45cm wide & 12mm thick)','cum.',123100.00),
('TN_SOR_2025','D',NULL,'M-0143','TW Planks (30-45cm wide & 12mm thick)','cum.',114300.00),
('TN_SOR_2025','D',NULL,'M-0144','TW Planks (30-45cm wide & 12-25mm thick)','cum.',107000.00),
('TN_SOR_2025','D',NULL,'M-0145','TW Planks (30-45cm wide & 25-40mm thick)','cum.',102600.00),
('TN_SOR_2025','D',NULL,'M-0146','TW Planks (15-30cm wide & 12mm thick)','cum.',99900.00),
('TN_SOR_2025','D',NULL,'M-0147','TW Planks (15-30cm wide & 12-25mm thick)','cum.',95000.00),
('TN_SOR_2025','D',NULL,'M-0148','TW Planks (15-30cm wide & 25-40mm thick)','cum.',93100.00),
('TN_SOR_2025','D',NULL,'M-0149','TW Planks (upto 15cm wide & 12mm thick)','cum.',91300.00),
('TN_SOR_2025','D',NULL,'M-0150','TW Planks (upto 15cm wide & 12-25mm thick)','cum.',91300.00),
('TN_SOR_2025','D',NULL,'M-0151','TW Planks (upto 15cm wide & 25-40mm thick)','cum.',86200.00),
('TN_SOR_2025','D',NULL,'M-0152','Seasoned Teakwood for Scantling and Planks for Heritage Works','cum.',185200.00),

('TN_SOR_2025','D','Teak Wood Reepers','M-0153','TW Reepers 50 x 25mm','RM',76.00),
('TN_SOR_2025','D','Teak Wood Reepers','M-0154','TW Reepers 50 x 12mm','RM',61.00),

('TN_SOR_2025','D','Country Wood Scantlings','M-0155','CW Scantling (upto 4m in length)','cum.',34300.00),
('TN_SOR_2025','D','Country Wood Scantlings','M-0156','CW Scantling (over 4m in length)','cum.',36200.00),
('TN_SOR_2025','D','Country Wood Scantlings','M-0157','CW Scantling (for tie beams & principal rafters for trusses)','cum.',36200.00),
('TN_SOR_2025','D','Country Wood Scantlings','M-0158','Jack Wood Scantlings (upto 4m)','cum.',37900.00),
('TN_SOR_2025','D','Country Wood Scantlings','M-0159','Silver Oak Scantlings','cum.',15500.00),

('TN_SOR_2025','D','Country Wood Planks','M-0160','CW Planks (upto 30cm wide-40mm thick)','cum.',39400.00),
('TN_SOR_2025','D','Country Wood Planks','M-0161','CW Planks (upto 30cm wide-25mm thick)','cum.',39400.00),
('TN_SOR_2025','D','Country Wood Planks','M-0162','CW Planks (over 30cm wide-40mm thick)','cum.',39400.00),
('TN_SOR_2025','D','Country Wood Planks','M-0163','CW Planks (over 30cm wide-25mm thick)','cum.',39400.00),
('TN_SOR_2025','D','Country Wood Planks','M-0164','JW Planks (25-40mm thick)','cum.',41300.00),
('TN_SOR_2025','D','Country Wood Planks','M-0165','Silver Oak Plank (40mm thick)','cum.',17600.00),
('TN_SOR_2025','D','Country Wood Planks','M-0166','Bluegum Plank','cum.',18100.00),

('TN_SOR_2025','D','Country Wood Reepers','M-0167','CW Reepers (50 x 25mm)','RM',34.60),
('TN_SOR_2025','D','Country Wood Reepers','M-0168','CW Reepers (50 x 12mm)','RM',24.90),
('TN_SOR_2025','D','Country Wood Reepers','M-0169','Mango Plank','cum.',16700.00),
('TN_SOR_2025','D','Country Wood Reepers','M-0170','Palmyrah Rafter (50-60mm wide & 125mm depth)','RM',49.50),
('TN_SOR_2025','D','Country Wood Reepers','M-0171','Palmyrah Leaves','100 Nos.',255.00),
('TN_SOR_2025','D','Country Wood Reepers','M-0172','Palmyrah Leaves (labour for cutting)','100 Nos.',40.20),

('TN_SOR_2025','D','Casurina Poles','M-0173','Casurina Poles 13cm-15cm dia','RM',33.00),
('TN_SOR_2025','D','Casurina Poles','M-0174','Casurina Poles 10cm-13cm dia','RM',25.20),
('TN_SOR_2025','D','Casurina Poles','M-0175','Casurina Poles 8cm-10cm dia','RM',19.20),
('TN_SOR_2025','D','Casurina Poles','M-0176','Casurina Poles 5cm-8cm dia','RM',17.50),

('TN_SOR_2025','D','Eucalyptus Poles','M-0177','13cm to 15cm dia','RM',33.00),
('TN_SOR_2025','D','Eucalyptus Poles','M-0178','10cm to 13cm dia','RM',23.60),
('TN_SOR_2025','D','Eucalyptus Poles','M-0179','8cm to 10cm dia','RM',19.20),
('TN_SOR_2025','D','Eucalyptus Poles','M-0180','5cm to 8cm dia','RM',16.40),
('TN_SOR_2025','D','Eucalyptus Poles','M-0181','Below 5cm','RM',15.00),
('TN_SOR_2025','D','Eucalyptus Poles','M-0182','Eucalyptus Bullies 4cm to 5cm dia and cross ties','RM',12.00),
('TN_SOR_2025','D','Eucalyptus Poles','M-0183','Casurina Bullies 4cm-5cm dia & cross ties','RM',13.50),
('TN_SOR_2025','D','Eucalyptus Poles','M-0184','Bamboo Large (10cm dia and above)','RM',12.00),
('TN_SOR_2025','D','Eucalyptus Poles','M-0185','Bamboo (7.5cm-10cm dia)','RM',10.60);

INSERT INTO sor_material_data
(sor_code,category_code,subcategory_name,unique_code,description,unit,base_rate)
VALUES
('TN_SOR_2025','E',NULL,'M-0186','Mild Steel Plates or Sheets BG 10','Kg',53.00),
('TN_SOR_2025','E',NULL,'M-0187','Mild Steel Angles 25 x 25 x 3 mm','Kg',53.00),
('TN_SOR_2025','E',NULL,'M-0188','Binding Wire (Black 18 G)','Kg',56.35),
('TN_SOR_2025','E',NULL,'M-0189','Binding Wire (Galvanised-18 G)','Kg',56.35),
('TN_SOR_2025','E',NULL,'M-0190','GI Sheets 30cm wide and 1.6mm thick','sqm.',391.10),
('TN_SOR_2025','E',NULL,'M-0191','Weld Mesh 7.5 x 2.5cm 10 Gauge','sqm.',379.90),
('TN_SOR_2025','E',NULL,'M-0192','Weld Mesh 7.5 x 5cm 10 Gauge','sqm.',339.60),
('TN_SOR_2025','E',NULL,'M-0193','Weld Mesh 10 x 10cm 10 Gauge','sqm.',183.80),
('TN_SOR_2025','E',NULL,'M-0194','Chicken Mesh','sqm.',40.65),
('TN_SOR_2025','E',NULL,'M-0195','Fly Proof Mesh','sqm.',116.55),
('TN_SOR_2025','E',NULL,'M-0196','Supplying Mild Steel Grills for windows, ventilators, etc., including priming coat','Kg',70.15);

INSERT INTO sor_material_data
(sor_code,category_code,subcategory_name,unique_code,description,unit,base_rate)
VALUES
('TN_SOR_2025','F',NULL,'M-2281','Heritage Mangalore Tiles size 10 x 16','1000 Nos',44000.00),
('TN_SOR_2025','F',NULL,'M-2282','ISMB steel girder of all section for roof beams & Columns','Kg.',135.00),
('TN_SOR_2025','F',NULL,'M-2283','Cement bonded particle Board 10mm thick','sqm.',470.00),
('TN_SOR_2025','F',NULL,'M-2284','SBR Chemical Liquid (Synthetic Butadine Rubber polymer) (water proofing compound)','Litre',800.00),
('TN_SOR_2025','F',NULL,'M-2285','SBR water proofing sheet 3 to 4mm With Geo Textiles 2 layer','sqm.',700.00),
('TN_SOR_2025','F',NULL,'M-2286','Damp Proof chemical using Water based epoxy resin','Kg.',600.00),
('TN_SOR_2025','F',NULL,'M-2287','Hydralic Double pressed fine grinded Interior grade Flooring clay tiles of size 150mm x 150mm x 20mm','each',18.00),
('TN_SOR_2025','F',NULL,'M-2288','Heritage Patterned customized cement based designer tiles of size 200mm x 200mm x 20mm including corner & inner border tiles','sqm.',4520.00),
('TN_SOR_2025','F',NULL,'M-2289','Cleaning cut stones using mild hydrofloric acid and powder and water pressure','sqm.',350.00),
('TN_SOR_2025','F',NULL,'M-2290','Applying lead pointing in Natural stone masonry & Flooring joints 20mm thick','RM',1000.00),
('TN_SOR_2025','F',NULL,'M-2291','White Marble powder for Heritage works','Kg.',75.00),
('TN_SOR_2025','F',NULL,'M-2292','Multi Colour glass panes with Antique pattern Hitching ornamental jaffri work 4mm thick','sqm.',1500.00),
('TN_SOR_2025','F',NULL,'M-2293','Hire and Running charges for Electrically Operated hoisting machine of capacity 200 - 300 Kg for period of one month','1 No.',4000.00),

('TN_SOR_2025','F','Seasoned Teakwood Scantlings and Planks for Heritage Works','M-2294','Upto 4m length','cum.',185200.00),
('TN_SOR_2025','F','Seasoned Teakwood Scantlings and Planks for Heritage Works','M-2295','4m to 6m length','cum.',297500.00),

('TN_SOR_2025','F','FAT LIME Putty with following Specifications - CaO content more than 90% and lime concentration 60-62% by weight with infinite shelf life when stored under water','M-2296','Fat Lime','Kg.',16.00),
('TN_SOR_2025','F','FAT LIME Putty with following Specifications - CaO content more than 90% and lime concentration 60-62% by weight with infinite shelf life when stored under water','M-2297','Ash','Kg.',9.00),
('TN_SOR_2025','F','FAT LIME Putty with following Specifications - CaO content more than 90% and lime concentration 60-62% by weight with infinite shelf life when stored under water','M-2298','Play (Coarse)','Kg.',100.00),
('TN_SOR_2025','F','FAT LIME Putty with following Specifications - CaO content more than 90% and lime concentration 60-62% by weight with infinite shelf life when stored under water','M-2299','Play (Fine)','Kg.',120.00),
('TN_SOR_2025','F','FAT LIME Putty with following Specifications - CaO content more than 90% and lime concentration 60-62% by weight with infinite shelf life when stored under water','M-2300','Play (Top)','Kg.',80.00),
('TN_SOR_2025','F','FAT LIME Putty with following Specifications - CaO content more than 90% and lime concentration 60-62% by weight with infinite shelf life when stored under water','M-2301','(Anti) Paint','Kg.',341.00),
('TN_SOR_2025','F','FAT LIME Putty with following Specifications - CaO content more than 90% and lime concentration 60-62% by weight with infinite shelf life when stored under water','M-2302','Pigment','Kg.',950.00),
('TN_SOR_2025','F','FAT LIME Putty with following Specifications - CaO content more than 90% and lime concentration 60-62% by weight with infinite shelf life when stored under water','M-2303','Play (Soap)','Kg.',360.00),
('TN_SOR_2025','F','FAT LIME Putty with following Specifications - CaO content more than 90% and lime concentration 60-62% by weight with infinite shelf life when stored under water','M-2304','ecoWAX (Protective Coat)','Kg.',490.00),
('TN_SOR_2025','F','FAT LIME Putty with following Specifications - CaO content more than 90% and lime concentration 60-62% by weight with infinite shelf life when stored under water','M-2305','Boosters','Kg.',920.00);


INSERT INTO sor_material_data
(sor_code,category_code,subcategory_name,unique_code,description,unit,base_rate)
VALUES
('TN_SOR_2025','ECBC','Specification for Burnt Clay Hollow Bricks for Walls','M-2306','Burnt Clay Hollow Brick (as per IS 3952-1988) with Rockwool Infill for Insulation for Walls, size 400 mm x 200 mm x 200 mm, U Value 0.6 W/m2K or lower','Nos.',165.00),

('TN_SOR_2025','ECBC','Specification for Burnt Clay Hollow Bricks for Walls','M-2307','Burnt Clay Hollow Brick (as per IS 3952-1988) for Walls, size 400 mm x 200 mm x 200 mm, U Value 1.00 W/m2K or lower','Nos.',72.00),

('TN_SOR_2025','ECBC','Specification for Burnt Clay Hollow Bricks for Walls','M-2308','Burnt Clay Hollow Brick (as per IS 3952-1988) for Walls, size 400 mm x 150 mm x 200 mm, U Value 1.20 W/m2K or lower','Nos.',60.00),

('TN_SOR_2025','ECBC','Specification for Burnt Clay Hollow Bricks for Walls','M-2309','Burnt Clay Hollow Brick (as per IS 3952-1988) for Walls and Partition Walls, size 400 mm x 100 mm x 200 mm, U Value 1.70 W/m2K or lower','Nos.',45.00),

('TN_SOR_2025','ECBC','Autoclaved Cellular Aerated Concrete Panel','M-2310','Supply of 50 mm thick AAC Prefabricated Fibre Reinforced Sandwich Panels having Thermal Conductivity 0.18 W/m.k or less','sqm.',590.00),

('TN_SOR_2025','ECBC','Autoclaved Cellular Aerated Concrete Panel','M-2311','Supply of 75 mm thick AAC Prefabricated Fibre Reinforced Sandwich Panels having Thermal Conductivity 0.17 W/m.k or less','sqm.',810.00);


# package table

CREATE TABLE work_item_package (
    id INT AUTO_INCREMENT PRIMARY KEY,

    sor_code VARCHAR(50),
    package_code VARCHAR(5),
    package_name VARCHAR(255),

    UNIQUE (sor_code, package_code),

    FOREIGN KEY (sor_code) REFERENCES sor_data(sor_code)
);
# subpackage table

CREATE TABLE work_item_subpackage (
    id INT AUTO_INCREMENT PRIMARY KEY,

    sor_code VARCHAR(50),
    package_code VARCHAR(5),

    subpackage_code VARCHAR(10),
    subpackage_name VARCHAR(255),
    description TEXT,

    UNIQUE (sor_code, subpackage_code),

    FOREIGN KEY (sor_code)
        REFERENCES sor_data(sor_code),

    FOREIGN KEY (sor_code, package_code)
        REFERENCES work_item_package(sor_code, package_code)
);

# rate table

CREATE TABLE work_item_rate (
    id INT AUTO_INCREMENT PRIMARY KEY,

    sor_code VARCHAR(50),
    subpackage_code VARCHAR(10),

    amount DECIMAL(14,2),

    UNIQUE (sor_code, subpackage_code),

    FOREIGN KEY (sor_code)
        REFERENCES sor_data(sor_code),

    FOREIGN KEY (sor_code, subpackage_code)
        REFERENCES work_item_subpackage(sor_code, subpackage_code)
);

INSERT INTO work_item_package (sor_code, package_code, package_name) VALUES
('TN_SOR_2025','A','Earth Work'),
('TN_SOR_2025','B','PCC Work'),
('TN_SOR_2025','C','RCC Work'),
('TN_SOR_2025','D','Masonry Work'),
('TN_SOR_2025','E','Plastering Work'),
('TN_SOR_2025','F','Flooring Work'),
('TN_SOR_2025','G','Painting Work'),
('TN_SOR_2025','H','UPVC'),
('TN_SOR_2025','I','Fabrication Work');

ALTER TABLE work_item_subpackage
ADD COLUMN analysis_quantity DECIMAL(10,2) NULL,
ADD COLUMN analysis_unit VARCHAR(20) NULL;


INSERT INTO work_item_subpackage
(sor_code, package_code, subpackage_code, subpackage_name, description, analysis_quantity, analysis_unit)
VALUES
-- A: Earth Work
('TN_SOR_2025','A','A1','Earthwork',NULL,NULL,NULL),

-- B: PCC Work
('TN_SOR_2025','B','B1','PCC - M5','PCC M5 (1:5:10)',NULL,NULL),
('TN_SOR_2025','B','B2','PCC - M7.5','PCC M7.5 (1:4:8)',NULL,NULL),
('TN_SOR_2025','B','B3','PCC - M10','PCC M10 (1:3:6)',NULL,NULL),
('TN_SOR_2025','B','B4','PCC - M15','PCC M15 (1:2:4)',NULL,NULL),
('TN_SOR_2025','B','B5','PCC - M20','PCC M20 (1:1.5:3)',NULL,NULL),

-- C: RCC Work
('TN_SOR_2025','C','C1','RCC - M20','RCC M20 (1:1.5:3)',NULL,NULL),
('TN_SOR_2025','C','C2','RCC - M25','RCC M25 (1:1:2)',NULL,NULL),
('TN_SOR_2025','C','C3','RCC - M30','RCC M30 (1:0.75:1.5)',NULL,NULL),

-- D: Masonry Work
('TN_SOR_2025','D','D1','Burnt Brick (230mm X 115mm X 75mm)','Masonry Burnt Brick (230mm X 115mm X 75mm) with 1:6 CM mortar',NULL,NULL),
('TN_SOR_2025','D','D2','Cement Block (200mm X 200mm X 400mm)',NULL,NULL,NULL),
('TN_SOR_2025','D','D3','Cement Block (150mm X 200mm X 400mm)',NULL,NULL,NULL),
('TN_SOR_2025','D','D4','Cement Block (100mm X 200mm X 400mm)',NULL,NULL,NULL),
('TN_SOR_2025','D','D5','AAC Block (600mm X 200mm X 200mm)',NULL,NULL,NULL),
('TN_SOR_2025','D','D6','AAC Block (600mm X 200mm X 150mm)',NULL,NULL,NULL),
('TN_SOR_2025','D','D7','AAC Block (600mm X 200mm X 100mm)',NULL,NULL,NULL),
('TN_SOR_2025','D','D8','Flyash Block (600mm X 200mm X 100mm)',NULL,NULL,NULL),
('TN_SOR_2025','D','D9','Flyash Block (400mm X 200mm X 200mm)',NULL,NULL,NULL),
('TN_SOR_2025','D','D10','Flyash Block (230mm X 110mm X 70mm)',NULL,NULL,NULL),

-- E: Plastering Work
('TN_SOR_2025','E','E1','Plastering Mix 1:2 CM','Cement Mortor of 1:2 Plestering Mix for 20mm thick plastering',NULL,NULL),
('TN_SOR_2025','E','E2','Plastering Mix 1:3 CM','Cement Mortor of 1:3 Plestering Mix for 20mm thick plastering',NULL,NULL),
('TN_SOR_2025','E','E3','Plastering Mix 1:4 CM','Cement Mortor of 1:4 Plestering Mix for 20mm thick plastering',NULL,NULL),
('TN_SOR_2025','E','E4','Plastering Mix 1:5 CM','Cement Mortor of 1:5 Plestering Mix for 12mm thick plastering',NULL,NULL),
('TN_SOR_2025','E','E5','Plastering Mix 1:6 CM','Cement Mortor of 1:6 Plestering Mix for 12mm thick plastering',NULL,NULL),

-- F: Flooring Work
('TN_SOR_2025','F','F1','Marble',NULL,NULL,NULL),
('TN_SOR_2025','F','F2','Granite',NULL,NULL,NULL),
('TN_SOR_2025','F','F3','Tile',NULL,NULL,NULL),

-- G: Painting Work
('TN_SOR_2025','G','G1','Internal Wall Painting',NULL,NULL,NULL),
('TN_SOR_2025','G','G2','Ceiling Painting',NULL,NULL,NULL),
('TN_SOR_2025','G','G3','External Wall Painting',NULL,NULL,NULL),

-- H: UPVC
('TN_SOR_2025','H','H1','Doors',NULL,NULL,NULL),
('TN_SOR_2025','H','H2','Windows',NULL,NULL,NULL),

-- I: Fabrication Work
('TN_SOR_2025','I','I1','SS',NULL,NULL,NULL),
('TN_SOR_2025','I','I2','MS',NULL,NULL,NULL),
('TN_SOR_2025','I','I3','Aluminium',NULL,NULL,NULL);


INSERT INTO work_item_rate (sor_code, subpackage_code, amount)
SELECT 'TN_SOR_2025', subpackage_code, 0
FROM work_item_subpackage
WHERE sor_code = 'TN_SOR_2025';

CREATE TABLE work_item_charges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    charge_name VARCHAR(255),
    percentage DECIMAL(5,2)
);

INSERT INTO work_item_charges (charge_name,percentage) VALUES
('Water Charges',1.50),
('Electrical Charges',1.00),
('Local Liaisoning & Dispute',0.50),
('Supervision Charges',1.00),
('Engineering & Testing Charges',0.50),
('Site Establishment',0.50),
('Insurance (Labour & Equipments)',0.50),
('Contingency, Safety Compliance & Overhead',5.00),
('Profit',10.00);

CREATE TABLE work_item_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,

    sor_code VARCHAR(50),
    subpackage_code VARCHAR(10),

    resource_type ENUM('MATERIAL','LABOUR','EQUIPMENT'),

    material_code VARCHAR(20) NULL,
    labour_code VARCHAR(20) NULL,

    quantity DECIMAL(12,3),

    remark VARCHAR(255),

    FOREIGN KEY (sor_code)
        REFERENCES sor_data(sor_code),

    FOREIGN KEY (sor_code, subpackage_code)
        REFERENCES work_item_subpackage(sor_code, subpackage_code),

    FOREIGN KEY (material_code)
        REFERENCES sor_material_data(unique_code),

    FOREIGN KEY (labour_code)
        REFERENCES sor_labour_data(unique_code)
);

ALTER TABLE work_item_analysis
ADD item VARCHAR(255) AFTER resource_type;

ALTER TABLE work_item_analysis
ADD equipment_code VARCHAR(20) NULL;

ALTER TABLE work_item_analysis
MODIFY equipment_code VARCHAR(20) NULL
AFTER labour_code;

ALTER TABLE sor_material_data
ADD unit_multiplier INT DEFAULT 1 AFTER unit;

ALTER TABLE sor_labour_data
ADD unit_multiplier INT DEFAULT 1 AFTER unit;

SET SQL_SAFE_UPDATES = 0;
UPDATE sor_material_data
SET unit_multiplier =
CASE
    WHEN unit LIKE '1000%' THEN 1000
    WHEN unit LIKE '100 Nos%' THEN 100
    ELSE 1
END;
SET SQL_SAFE_UPDATES = 1;

SET SQL_SAFE_UPDATES = 0;
UPDATE sor_material_data
SET unit =
CASE
    WHEN unit LIKE '%Nos%' THEN 'Nos'
    WHEN unit LIKE '%Kg%' THEN 'Kg'
    WHEN unit LIKE '%cum%' THEN 'cum'
    WHEN unit LIKE '%sqm%' THEN 'sqm'
    WHEN unit LIKE '%RM%' THEN 'RM'
    ELSE unit
END;
SET SQL_SAFE_UPDATES = 1;

CREATE TABLE IF NOT EXISTS sor_equipment_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sor_code VARCHAR(50) NOT NULL,
    unique_code VARCHAR(20) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    unit VARCHAR(50) NOT NULL,
    base_rate DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sor_code) REFERENCES sor_data(sor_code)
);

INSERT INTO sor_equipment_data (sor_code, unique_code, description, unit, base_rate) VALUES
('TN_SOR_2025','H-0097','Pumping charges of concrete including hire charges of pump piping work and accessories etc.','cum.',268.40),
('TN_SOR_2025','H-0098','Carriage of concrete by Transit Mixer','Km / Cum',38.06),
('TN_SOR_2025','H-0099','Cutting Saw Machine','Day',1729.20),
('TN_SOR_2025','H-0100','Concrete Jount Cutting Machine','Day',1152.80),
('TN_SOR_2025','H-0101','Air Compressor 250 cfm. with two leads for Pneumatic Cutters / Hammers','Day',2050.40),
('TN_SOR_2025','H-0102','Excavation of diaphragm wall by Mechanical Grab','Day',1666.50),
('TN_SOR_2025','H-0103','Hire and running charges of Bentonite Pump','Day',4485.80),
('TN_SOR_2025','H-0104','Hire and running charges of Crane 20 Tonne capacity','Day',8970.50),
('TN_SOR_2025','H-0105','Hire and running charges of Crane 40 Tonne capacity','Day',10252.00),
('TN_SOR_2025','H-0106','Hire and running charges of Crane 80 Tonne capacity','Day',19228.00),
('TN_SOR_2025','H-0107','Tractor with Trailar including Driver and Fuel','Hour',600.00),
('TN_SOR_2025','H-0108','Earth Excavator- Wheeled Backhoe loader 0.50 m3 capacity','Hour',784.00),
('TN_SOR_2025','H-0109','Hire Charges for Surface Vibrator or Earth Rammer including Fuel','Day',1000.00),
('TN_SOR_2025','H-0110','Mixer Machine with Hopper','Day',1500.00),
('TN_SOR_2025','H-0111','Earth Excavator- Crawler / Tracked Excavator 1 m3 capacity','Hour',2000.00),
('TN_SOR_2025','H-0112','Hire running charges for hydraulic piling Rigs including power accessories shifting from place to place','Hour',4000.00),
('TN_SOR_2025','H-0113','Hire running charges for Light Crane','Hour',625.00),
('TN_SOR_2025','H-0114','Hire running charges for Tipper','Hour',938.00),
('TN_SOR_2025','H-0115','Hire running charges for Loader','Hour',729.00),
('TN_SOR_2025','H-0116','Hire charges for Excavation Tools and Tackles','Day',500.00),
('TN_SOR_2025','H-0117','Hire charges for Masonry Tools and Tackles','Day',450.00),
('TN_SOR_2025','H-0118','Hire charges for Masonry Scaffolding','Day',750.00),
('TN_SOR_2025','H-0119','Hire charges for Concrete Formwork','Day',2500.00),
('TN_SOR_2025','H-0120','Hire charges for Concrete Shuttering','Day',3000.00),
('TN_SOR_2025','H-0121','Hire charges for Concrete Tools and Tackles','Day',2000.00);


ALTER TABLE sor_equipment_data
DROP COLUMN created_at;

USE arch_db;

-- Optional: clear old rows for these items first
DELETE FROM work_item_analysis
WHERE sor_code = 'TN_SOR_2025'
  AND subpackage_code IN ('C3','D1','E3','E5');

INSERT INTO work_item_analysis
(sor_code, subpackage_code, resource_type, item, material_code, labour_code, equipment_code, quantity, remark)
VALUES
-- =========================
-- C3 : RCC M30 (1:0.75:1.5)
-- =========================
('TN_SOR_2025','C3','MATERIAL','Coarse Aggregate','M-0088',NULL,NULL,8.000,NULL),
('TN_SOR_2025','C3','MATERIAL','Fine Aggragete','M-0125',NULL,NULL,4.000,NULL),
('TN_SOR_2025','C3','MATERIAL','Cement  (96 bags or 3.33 Cu.M)','M-0001',NULL,NULL,4.800,NULL),
('TN_SOR_2025','C3','MATERIAL','Steel, Mild Steel bars @ 2% = 0.2 Cu.M','M-0002',NULL,NULL,1.570,'1 Cu.M of steel = 78.5 Quintals; 78.5Q x 0.2Cu.M = 15.7Q; 1Q = 0.1 MT'),
('TN_SOR_2025','C3','MATERIAL','Binding Wire','M-0189',NULL,NULL,2.000,NULL),

('TN_SOR_2025','C3','LABOUR','Mistri (Head Mason)',NULL,'L-0029',NULL,1.000,NULL),
('TN_SOR_2025','C3','LABOUR','Mason',NULL,'L-0029',NULL,3.000,NULL),
('TN_SOR_2025','C3','LABOUR','Male Coolie',NULL,'L-0073',NULL,4.000,NULL),
('TN_SOR_2025','C3','LABOUR','Female Coolie',NULL,'L-0098',NULL,4.000,NULL),
('TN_SOR_2025','C3','LABOUR','Blacksmith (II class) for bar bending',NULL,'L-0060',NULL,8.000,NULL),
('TN_SOR_2025','C3','LABOUR','Mazdoor for bar bending',NULL,'L-0098',NULL,8.000,NULL),
('TN_SOR_2025','C3','LABOUR','Carpenter (II class) for centering & shuttering',NULL,'L-0063',NULL,10.000,NULL),
('TN_SOR_2025','C3','LABOUR','Mazdoor for centering & shuttering',NULL,'L-0098',NULL,10.000,NULL),

('TN_SOR_2025','C3','EQUIPMENT','Concrete Mixer',NULL,NULL,'H-0110',0.750,NULL),
('TN_SOR_2025','C3','EQUIPMENT','Vibrator',NULL,NULL,'H-0109',1.000,NULL),
('TN_SOR_2025','C3','EQUIPMENT','Formwork',NULL,NULL,'H-0119',1.000,NULL),
('TN_SOR_2025','C3','EQUIPMENT','Shuttering',NULL,NULL,'H-0120',1.000,NULL),
('TN_SOR_2025','C3','EQUIPMENT','Tools and Tackles',NULL,NULL,'H-0121',1.000,NULL),

-- ============================================
-- D1 : Masonry Burnt Brick with 1:6 CM mortar
-- ============================================
('TN_SOR_2025','D1','MATERIAL','Brick (500 bricks per Cu.M)','M-0003',NULL,NULL,5000.000,NULL),
('TN_SOR_2025','D1','MATERIAL','Cement (13.5 bags or 0.45 Cu.M)','M-0001',NULL,NULL,0.648,'Weight = Volume x Density = 0.45 x 1440'),
('TN_SOR_2025','D1','MATERIAL','Fine Aggregate','M-0125',NULL,NULL,2.700,NULL),

('TN_SOR_2025','D1','LABOUR','Mistri (Head Mason)',NULL,'L-0029',NULL,1.000,NULL),
('TN_SOR_2025','D1','LABOUR','Mason',NULL,'L-0029',NULL,10.000,NULL),
('TN_SOR_2025','D1','LABOUR','Male Coolie',NULL,'L-0073',NULL,10.000,NULL),
('TN_SOR_2025','D1','LABOUR','Female Coolie',NULL,'L-0098',NULL,7.000,NULL),

('TN_SOR_2025','D1','EQUIPMENT','Scaffolding',NULL,NULL,'H-0118',1.000,NULL),
('TN_SOR_2025','D1','EQUIPMENT','Tools and Tackles',NULL,NULL,'H-0117',1.000,NULL),

-- ==========================================
-- E3 : Cement Mortor 1:4 (20mm plastering)
-- ==========================================
('TN_SOR_2025','E3','MATERIAL','Cement (19.5 bags or 0.65 Cu.M)','M-0001',NULL,NULL,0.936,NULL),
('TN_SOR_2025','E3','MATERIAL','Fine Aggregate','M-0126',NULL,NULL,2.600,NULL),

('TN_SOR_2025','E3','LABOUR','Mistri (Head Mason)',NULL,'L-0029',NULL,1.000,NULL),
('TN_SOR_2025','E3','LABOUR','Mason',NULL,'L-0029',NULL,10.000,NULL),
('TN_SOR_2025','E3','LABOUR','Male Coolie',NULL,'L-0073',NULL,10.000,NULL),
('TN_SOR_2025','E3','LABOUR','Female Coolie',NULL,'L-0098',NULL,5.000,NULL),

('TN_SOR_2025','E3','EQUIPMENT','Scaffolding',NULL,NULL,'H-0118',1.000,NULL),
('TN_SOR_2025','E3','EQUIPMENT','Tools and Tackles',NULL,NULL,'H-0117',1.000,NULL),

-- ==========================================
-- E5 : Cement Mortor 1:6 (12mm plastering)
-- ==========================================
('TN_SOR_2025','E5','MATERIAL','Cement (9 bags or 0.30 Cu.M)','M-0001',NULL,NULL,0.432,NULL),
('TN_SOR_2025','E5','MATERIAL','Fine Aggregate','M-0126',NULL,NULL,1.800,NULL),

('TN_SOR_2025','E5','LABOUR','Mistri (Head Mason)',NULL,'L-0029',NULL,1.000,NULL),
('TN_SOR_2025','E5','LABOUR','Mason',NULL,'L-0029',NULL,10.000,NULL),
('TN_SOR_2025','E5','LABOUR','Male Coolie',NULL,'L-0073',NULL,10.000,NULL),
('TN_SOR_2025','E5','LABOUR','Female Coolie',NULL,'L-0098',NULL,5.000,NULL),

('TN_SOR_2025','E5','EQUIPMENT','Scaffolding',NULL,NULL,'H-0118',1.000,NULL),
('TN_SOR_2025','E5','EQUIPMENT','Tools and Tackles',NULL,NULL,'H-0117',1.000,NULL);

UPDATE work_item_subpackage
SET
    analysis_quantity = 10,
    analysis_unit = 'Cu.M'
WHERE sor_code = 'TN_SOR_2025'
  AND subpackage_code IN ('C3', 'D1');

UPDATE work_item_subpackage
SET
    analysis_quantity = 100,
    analysis_unit = 'Cu.M'
WHERE sor_code = 'TN_SOR_2025'
  AND subpackage_code IN ('E3', 'E5');

USE arch_db;

-- Drop old (if any)
DROP TABLE IF EXISTS lead_lift_rate_detail;
DROP TABLE IF EXISTS lead_lift_item_master;

-- 1) Item master (your 5 working items)
CREATE TABLE lead_lift_item_master (
    sor_code VARCHAR(50) NOT NULL,
    ll_code VARCHAR(10) NOT NULL,              -- LL1..LL5
    item_name VARCHAR(180) NOT NULL,
    profile_code VARCHAR(10) NOT NULL,         -- TP1..TP6 mapping
    distance_km DECIMAL(10,2) NOT NULL,        -- editable project distance

    PRIMARY KEY (sor_code, ll_code),
    UNIQUE KEY uq_ll_item (sor_code, item_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2) Rate detail (all top-grid data: coefficient, lift, slab rates)
CREATE TABLE lead_lift_rate_detail (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sor_code VARCHAR(50) NOT NULL,
    profile_code VARCHAR(10) NOT NULL,
    profile_name VARCHAR(255) NOT NULL,
    unit VARCHAR(50) NOT NULL,

    coefficient DECIMAL(10,4) NOT NULL,
    incidental_charges DECIMAL(12,2) NOT NULL DEFAULT 0,
    loading_charges DECIMAL(12,2) NOT NULL DEFAULT 0,
    unloading_charges DECIMAL(12,2) NOT NULL DEFAULT 0,

    slab_order TINYINT NOT NULL,               -- 1..5
    slab_from_km DECIMAL(10,2) NOT NULL,
    slab_to_km DECIMAL(10,2) NULL,             -- NULL => Above 80
    rate_per_km DECIMAL(12,2) NOT NULL,

    UNIQUE KEY uq_profile_slab (sor_code, profile_code, slab_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO lead_lift_item_master (sor_code, ll_code, item_name, profile_code, distance_km)
VALUES
('TN_SOR_2025','LL1','Cement','TP1',15.00),
('TN_SOR_2025','LL2','Steel','TP1',11.00),
('TN_SOR_2025','LL3','Course Aggregate','TP3',20.00),
('TN_SOR_2025','LL4','Fine Aggregate','TP3',25.00),
('TN_SOR_2025','LL5','Burnt Brick (230mm X 115mm X 75mm)','TP6',15.00);

INSERT INTO lead_lift_rate_detail
(sor_code, profile_code, profile_name, unit, coefficient, incidental_charges, loading_charges, unloading_charges, slab_order, slab_from_km, slab_to_km, rate_per_km)
VALUES
-- TP1
('TN_SOR_2025','TP1','Cement, Steel (1 MT)','MT',1.00,0.00,135.50,135.50,1,0.00,10.00,7.36),
('TN_SOR_2025','TP1','Cement, Steel (1 MT)','MT',1.00,0.00,135.50,135.50,2,10.00,20.00,6.30),
('TN_SOR_2025','TP1','Cement, Steel (1 MT)','MT',1.00,0.00,135.50,135.50,3,20.00,40.00,5.42),
('TN_SOR_2025','TP1','Cement, Steel (1 MT)','MT',1.00,0.00,135.50,135.50,4,40.00,80.00,4.66),
('TN_SOR_2025','TP1','Cement, Steel (1 MT)','MT',1.00,0.00,135.50,135.50,5,80.00,NULL,4.26),

-- TP2
('TN_SOR_2025','TP2','Lime Stone, Laterite, Brick Jelly, Wood Work, Pond Ash (Wet / Dry), Stone Dust (1Cu.M)','Cu.M',1.10,0.00,64.65,64.65,1,0.00,10.00,8.08),
('TN_SOR_2025','TP2','Lime Stone, Laterite, Brick Jelly, Wood Work, Pond Ash (Wet / Dry), Stone Dust (1Cu.M)','Cu.M',1.10,0.00,64.65,64.65,2,10.00,20.00,6.92),
('TN_SOR_2025','TP2','Lime Stone, Laterite, Brick Jelly, Wood Work, Pond Ash (Wet / Dry), Stone Dust (1Cu.M)','Cu.M',1.10,0.00,64.65,64.65,3,20.00,40.00,5.97),
('TN_SOR_2025','TP2','Lime Stone, Laterite, Brick Jelly, Wood Work, Pond Ash (Wet / Dry), Stone Dust (1Cu.M)','Cu.M',1.10,0.00,64.65,64.65,4,40.00,80.00,5.15),
('TN_SOR_2025','TP2','Lime Stone, Laterite, Brick Jelly, Wood Work, Pond Ash (Wet / Dry), Stone Dust (1Cu.M)','Cu.M',1.10,0.00,64.65,64.65,5,80.00,NULL,4.69),

-- TP3
('TN_SOR_2025','TP3','Rough Stone, Bond Stone, Cut Stone, Broken Stone Jelly, Sand, Gravel, Surki, Earth, Crushed Stone Sand (1Cu.M)','Cu.M',1.60,0.00,44.25,44.25,1,0.00,10.00,11.79),
('TN_SOR_2025','TP3','Rough Stone, Bond Stone, Cut Stone, Broken Stone Jelly, Sand, Gravel, Surki, Earth, Crushed Stone Sand (1Cu.M)','Cu.M',1.60,0.00,44.25,44.25,2,10.00,20.00,10.08),
('TN_SOR_2025','TP3','Rough Stone, Bond Stone, Cut Stone, Broken Stone Jelly, Sand, Gravel, Surki, Earth, Crushed Stone Sand (1Cu.M)','Cu.M',1.60,0.00,44.25,44.25,3,20.00,40.00,8.67),
('TN_SOR_2025','TP3','Rough Stone, Bond Stone, Cut Stone, Broken Stone Jelly, Sand, Gravel, Surki, Earth, Crushed Stone Sand (1Cu.M)','Cu.M',1.60,0.00,44.25,44.25,4,40.00,80.00,8.13),
('TN_SOR_2025','TP3','Rough Stone, Bond Stone, Cut Stone, Broken Stone Jelly, Sand, Gravel, Surki, Earth, Crushed Stone Sand (1Cu.M)','Cu.M',1.60,0.00,44.25,44.25,5,80.00,NULL,6.82),

-- TP4
('TN_SOR_2025','TP4','Third Class Country Bricks (Kiln Burnt) (1000 Nos.)','1000 Nos.',1.35,0.00,63.60,63.60,1,0.00,10.00,9.94),
('TN_SOR_2025','TP4','Third Class Country Bricks (Kiln Burnt) (1000 Nos.)','1000 Nos.',1.35,0.00,63.60,63.60,2,10.00,20.00,8.51),
('TN_SOR_2025','TP4','Third Class Country Bricks (Kiln Burnt) (1000 Nos.)','1000 Nos.',1.35,0.00,63.60,63.60,3,20.00,40.00,7.30),
('TN_SOR_2025','TP4','Third Class Country Bricks (Kiln Burnt) (1000 Nos.)','1000 Nos.',1.35,0.00,63.60,63.60,4,40.00,80.00,6.30),
('TN_SOR_2025','TP4','Third Class Country Bricks (Kiln Burnt) (1000 Nos.)','1000 Nos.',1.35,0.00,63.60,63.60,5,80.00,NULL,5.76),

-- TP5
('TN_SOR_2025','TP5','Mangalore Tiles (1000 Nos), Machine Pressed Tiles (2000 Nos), Hydraulically Pressed Mosaic Flooring Tiles (1500 Nos)','Nos.',1.80,0.00,63.60,63.60,1,0.00,10.00,13.26),
('TN_SOR_2025','TP5','Mangalore Tiles (1000 Nos), Machine Pressed Tiles (2000 Nos), Hydraulically Pressed Mosaic Flooring Tiles (1500 Nos)','Nos.',1.80,0.00,63.60,63.60,2,10.00,20.00,11.35),
('TN_SOR_2025','TP5','Mangalore Tiles (1000 Nos), Machine Pressed Tiles (2000 Nos), Hydraulically Pressed Mosaic Flooring Tiles (1500 Nos)','Nos.',1.80,0.00,63.60,63.60,3,20.00,40.00,9.76),
('TN_SOR_2025','TP5','Mangalore Tiles (1000 Nos), Machine Pressed Tiles (2000 Nos), Hydraulically Pressed Mosaic Flooring Tiles (1500 Nos)','Nos.',1.80,0.00,63.60,63.60,4,40.00,80.00,8.41),
('TN_SOR_2025','TP5','Mangalore Tiles (1000 Nos), Machine Pressed Tiles (2000 Nos), Hydraulically Pressed Mosaic Flooring Tiles (1500 Nos)','Nos.',1.80,0.00,63.60,63.60,5,80.00,NULL,7.68),

-- TP6
('TN_SOR_2025','TP6','Bricks II Class Chamber Burnt Bricks (Table Moulded / Ground Moulded), Fly Ash Bricks (1000 Nos.)','1000 Nos.',2.25,0.00,63.60,63.60,1,0.00,10.00,16.57),
('TN_SOR_2025','TP6','Bricks II Class Chamber Burnt Bricks (Table Moulded / Ground Moulded), Fly Ash Bricks (1000 Nos.)','1000 Nos.',2.25,0.00,63.60,63.60,2,10.00,20.00,14.19),
('TN_SOR_2025','TP6','Bricks II Class Chamber Burnt Bricks (Table Moulded / Ground Moulded), Fly Ash Bricks (1000 Nos.)','1000 Nos.',2.25,0.00,63.60,63.60,3,20.00,40.00,12.19),
('TN_SOR_2025','TP6','Bricks II Class Chamber Burnt Bricks (Table Moulded / Ground Moulded), Fly Ash Bricks (1000 Nos.)','1000 Nos.',2.25,0.00,63.60,63.60,4,40.00,80.00,10.52),
('TN_SOR_2025','TP6','Bricks II Class Chamber Burnt Bricks (Table Moulded / Ground Moulded), Fly Ash Bricks (1000 Nos.)','1000 Nos.',2.25,0.00,63.60,63.60,5,80.00,NULL,9.60);

SELECT
    i.item_name AS Items,
    i.distance_km AS `Distance (Km)`,
    ROUND(SUM(
        GREATEST(
            LEAST(i.distance_km, COALESCE(d.slab_to_km, i.distance_km)) - d.slab_from_km,
            0
        ) * d.rate_per_km
    ) + MAX(d.incidental_charges), 2) AS `Total Transport Charges`,
    ROUND(MAX(d.loading_charges + d.unloading_charges), 2) AS `Total Lift Charges`,
    ROUND(
        SUM(
            GREATEST(
                LEAST(i.distance_km, COALESCE(d.slab_to_km, i.distance_km)) - d.slab_from_km,
                0
            ) * d.rate_per_km
        ) + MAX(d.incidental_charges) + MAX(d.loading_charges + d.unloading_charges),
        2
    ) AS `Total Charges`
FROM lead_lift_item_master i
JOIN lead_lift_rate_detail d
  ON d.sor_code = i.sor_code
 AND d.profile_code = i.profile_code
WHERE i.sor_code = 'TN_SOR_2025'
GROUP BY i.ll_code, i.item_name, i.distance_km
ORDER BY i.ll_code;

USE arch_db;

-- 1) Extend resource_type enum
ALTER TABLE work_item_analysis
MODIFY resource_type ENUM('MATERIAL','LABOUR','EQUIPMENT','LEAD & LIFT') NOT NULL;

-- 2) Add lead_lift_code column
ALTER TABLE work_item_analysis
ADD lead_lift_code VARCHAR(10) NULL AFTER equipment_code;

-- 3) Add FK to LL master (sor_code + ll_code)
ALTER TABLE work_item_analysis
ADD CONSTRAINT fk_wia_lead_lift
FOREIGN KEY (sor_code, lead_lift_code)
REFERENCES lead_lift_item_master (sor_code, ll_code);

INSERT INTO work_item_analysis
(
  sor_code,
  subpackage_code,
  resource_type,
  item,
  material_code,
  labour_code,
  equipment_code,
  lead_lift_code,
  quantity,
  remark
)
VALUES
-- C3 (from C3 sheet Lead & Lift section)
('TN_SOR_2025','C3','LEAD & LIFT','Course Aggregate',NULL,NULL,NULL,'LL3',8.000,NULL),
('TN_SOR_2025','C3','LEAD & LIFT','Fine Aggregate',NULL,NULL,NULL,'LL4',4.000,NULL),
('TN_SOR_2025','C3','LEAD & LIFT','Cement',NULL,NULL,NULL,'LL1',4.800,NULL),
('TN_SOR_2025','C3','LEAD & LIFT','Steel',NULL,NULL,NULL,'LL2',1.570,NULL),

-- D1
('TN_SOR_2025','D1','LEAD & LIFT','Burnt Brick (230mm X 115mm X 75mm)',NULL,NULL,NULL,'LL5',5000.000,NULL),
('TN_SOR_2025','D1','LEAD & LIFT','Cement',NULL,NULL,NULL,'LL1',0.648,NULL),
('TN_SOR_2025','D1','LEAD & LIFT','Fine Aggregate',NULL,NULL,NULL,'LL4',2.700,NULL),

-- E3
('TN_SOR_2025','E3','LEAD & LIFT','Cement',NULL,NULL,NULL,'LL1',0.936,NULL),
('TN_SOR_2025','E3','LEAD & LIFT','Fine Aggregate',NULL,NULL,NULL,'LL4',2.600,NULL),

-- E5
('TN_SOR_2025','E5','LEAD & LIFT','Cement',NULL,NULL,NULL,'LL1',0.432,NULL),
('TN_SOR_2025','E5','LEAD & LIFT','Fine Aggregate',NULL,NULL,NULL,'LL4',1.800,NULL);

INSERT INTO work_item_rate (sor_code, subpackage_code, amount)
SELECT
    s.sor_code,
    s.subpackage_code,
    CEILING((t.total_a * (1 + cf.pct)) / s.analysis_quantity) AS rate_per_unit
FROM work_item_subpackage s
JOIN (
    SELECT
        a.sor_code,
        a.subpackage_code,
        SUM(
            CASE a.resource_type
                WHEN 'MATERIAL' THEN (a.quantity / COALESCE(m.unit_multiplier, 1)) * m.base_rate
                WHEN 'LABOUR'   THEN (a.quantity / COALESCE(l.unit_multiplier, 1)) * l.base_rate
                WHEN 'EQUIPMENT' THEN a.quantity * e.base_rate
                WHEN 'LEAD & LIFT' THEN (a.quantity / COALESCE(ll.unit_multiplier, 1)) * ll.total_charge_per_unit
                ELSE 0
            END
        ) AS total_a
    FROM work_item_analysis a
    LEFT JOIN sor_material_data  m
        ON a.resource_type = 'MATERIAL'
       AND a.material_code = m.unique_code
    LEFT JOIN sor_labour_data l
        ON a.resource_type = 'LABOUR'
       AND a.labour_code = l.unique_code
    LEFT JOIN sor_equipment_data e
        ON a.resource_type = 'EQUIPMENT'
       AND a.equipment_code = e.unique_code
    LEFT JOIN (
        SELECT
            i.sor_code,
            i.ll_code,
            CASE
                WHEN MAX(d.unit) LIKE '1000%' THEN 1000
                WHEN MAX(d.unit) LIKE '100 Nos%' THEN 100
                ELSE 1
            END AS unit_multiplier,
            ROUND(
                SUM(
                    GREATEST(
                        LEAST(i.distance_km, COALESCE(d.slab_to_km, i.distance_km)) - d.slab_from_km,
                        0
                    ) * d.rate_per_km
                )
                + MAX(d.incidental_charges)
                + MAX(d.loading_charges + d.unloading_charges),
                2
            ) AS total_charge_per_unit
        FROM lead_lift_item_master i
        JOIN lead_lift_rate_detail d
          ON d.sor_code = i.sor_code
         AND d.profile_code = i.profile_code
        WHERE i.sor_code = 'TN_SOR_2025'
        GROUP BY i.sor_code, i.ll_code
    ) ll
        ON a.resource_type = 'LEAD & LIFT'
       AND a.sor_code = ll.sor_code
       AND a.lead_lift_code = ll.ll_code
    WHERE a.sor_code = 'TN_SOR_2025'
      AND a.subpackage_code IN ('C3','D1','E3','E5')
    GROUP BY a.sor_code, a.subpackage_code
) t
    ON t.sor_code = s.sor_code
   AND t.subpackage_code = s.subpackage_code
CROSS JOIN (
    SELECT COALESCE(SUM(percentage), 0) / 100.0 AS pct
    FROM work_item_charges
) cf
WHERE s.sor_code = 'TN_SOR_2025'
  AND s.subpackage_code IN ('C3','D1','E3','E5')
  AND s.analysis_quantity IS NOT NULL
  AND s.analysis_quantity > 0
ON DUPLICATE KEY UPDATE amount = VALUES(amount);

USE arch_db;

-- =========================================================
-- 1) PROJECT MASTER TABLE
-- =========================================================
CREATE TABLE IF NOT EXISTS project_master (
    project_code VARCHAR(50) NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    project_location TEXT NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    site_area DECIMAL(18,3) NULL,
    total_builtup_area DECIMAL(18,3) NULL,
    building_height DECIMAL(18,3) NULL,
    date_of_issue DATE NULL,
    estimator_name VARCHAR(255) NOT NULL,
    ifc_file_name VARCHAR(255) NOT NULL,
    sor_database VARCHAR(100) NOT NULL,     -- example: TN_SOR_2025
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (project_code, ifc_file_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================================================
-- 2) MASONRY MATERIAL TAKE-OFF (from Wall.py shape)
-- =========================================================
CREATE TABLE IF NOT EXISTS masonry_material_takeoff (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_code VARCHAR(50) NOT NULL,
    ifc_file_name VARCHAR(255) NOT NULL,

    express_id BIGINT NOT NULL,             -- from Wall.py
    global_id VARCHAR(64) NULL,
    family VARCHAR(255) NULL,
    type_name VARCHAR(255) NULL,
    base_constraint VARCHAR(255) NULL,
    length_val DECIMAL(18,6) NULL,
    width_val DECIMAL(18,6) NULL,
    material_name VARCHAR(180) NOT NULL,
    material_description TEXT NULL,
    material_area DECIMAL(18,6) NULL,
    material_volume DECIMAL(18,6) NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_masonry_entry (project_code, ifc_file_name, express_id, material_name),
    KEY idx_masonry_proj_ifc (project_code, ifc_file_name),

    CONSTRAINT fk_masonry_proj
      FOREIGN KEY (project_code, ifc_file_name)
      REFERENCES project_master(project_code, ifc_file_name)
      ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================================================
-- 3) MASONRY SUMMARY
-- =========================================================
CREATE TABLE IF NOT EXISTS masonry_summary (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_code VARCHAR(50) NOT NULL,
    ifc_file_name VARCHAR(255) NOT NULL,

    material_name VARCHAR(180) NOT NULL,
    material_description TEXT NULL,
    total_material_area DECIMAL(18,6) NULL,
    total_material_volume DECIMAL(18,6) NULL,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_masonry_summary (project_code, ifc_file_name, material_name),
    KEY idx_masonry_summary_proj_ifc (project_code, ifc_file_name),

    CONSTRAINT fk_masonry_summary_proj
      FOREIGN KEY (project_code, ifc_file_name)
      REFERENCES project_master(project_code, ifc_file_name)
      ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================================================
-- 4) PLASTERING MATERIAL TAKE-OFF
-- (same structure as wall-derived takeoff for now)
-- =========================================================
CREATE TABLE IF NOT EXISTS plastering_material_takeoff (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_code VARCHAR(50) NOT NULL,
    ifc_file_name VARCHAR(255) NOT NULL,

    express_id BIGINT NOT NULL,
    global_id VARCHAR(64) NULL,
    family VARCHAR(255) NULL,
    type_name VARCHAR(255) NULL,
    base_constraint VARCHAR(255) NULL,
    length_val DECIMAL(18,6) NULL,
    width_val DECIMAL(18,6) NULL,
    material_name VARCHAR(180) NOT NULL,
    material_description TEXT NULL,
    material_area DECIMAL(18,6) NULL,
    material_volume DECIMAL(18,6) NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_plastering_entry (project_code, ifc_file_name, express_id, material_name),
    KEY idx_plastering_proj_ifc (project_code, ifc_file_name),

    CONSTRAINT fk_plastering_proj
      FOREIGN KEY (project_code, ifc_file_name)
      REFERENCES project_master(project_code, ifc_file_name)
      ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================================================
-- 5) PLASTERING SUMMARY
-- =========================================================
CREATE TABLE IF NOT EXISTS plastering_summary (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_code VARCHAR(50) NOT NULL,
    ifc_file_name VARCHAR(255) NOT NULL,

    material_name VARCHAR(180) NOT NULL,
    material_description TEXT NULL,
    total_material_area DECIMAL(18,6) NULL,
    total_material_volume DECIMAL(18,6) NULL,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_plastering_summary (project_code, ifc_file_name, material_name),
    KEY idx_plastering_summary_proj_ifc (project_code, ifc_file_name),

    CONSTRAINT fk_plastering_summary_proj
      FOREIGN KEY (project_code, ifc_file_name)
      REFERENCES project_master(project_code, ifc_file_name)
      ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================================================
-- 6) RCC MATERIAL TAKE-OFF (from RCC.py shape)
-- =========================================================
CREATE TABLE IF NOT EXISTS rcc_material_takeoff (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_code VARCHAR(50) NOT NULL,
    ifc_file_name VARCHAR(255) NOT NULL,

    express_id BIGINT NOT NULL,             -- from RCC.py
    global_id VARCHAR(64) NULL,
    family VARCHAR(255) NULL,
    type_name VARCHAR(255) NULL,
    level_name VARCHAR(255) NULL,
    material_name VARCHAR(180) NOT NULL,
    material_description TEXT NULL,
    material_volume DECIMAL(18,6) NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_rcc_entry (project_code, ifc_file_name, express_id, material_name),
    KEY idx_rcc_proj_ifc (project_code, ifc_file_name),

    CONSTRAINT fk_rcc_proj
      FOREIGN KEY (project_code, ifc_file_name)
      REFERENCES project_master(project_code, ifc_file_name)
      ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================================================
-- 7) RCC SUMMARY
-- =========================================================
CREATE TABLE IF NOT EXISTS rcc_summary (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_code VARCHAR(50) NOT NULL,
    ifc_file_name VARCHAR(255) NOT NULL,

    material_name VARCHAR(180) NOT NULL,
    material_description TEXT NULL,
    total_material_volume DECIMAL(18,6) NULL,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_rcc_summary (project_code, ifc_file_name, material_name),
    KEY idx_rcc_summary_proj_ifc (project_code, ifc_file_name),

    CONSTRAINT fk_rcc_summary_proj
      FOREIGN KEY (project_code, ifc_file_name)
      REFERENCES project_master(project_code, ifc_file_name)
      ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
