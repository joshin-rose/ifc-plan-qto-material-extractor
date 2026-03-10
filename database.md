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
('TN_SOR_2025','D','Reinforcement Work'),
('TN_SOR_2025','E','Masonry Work'),
('TN_SOR_2025','F','Plastering Work'),
('TN_SOR_2025','G','Flooring Work'),
('TN_SOR_2025','H','Painting Work'),
('TN_SOR_2025','I','UPVC'),
('TN_SOR_2025','J','Fabrication Work');

INSERT INTO work_item_subpackage
(sor_code, package_code, subpackage_code, subpackage_name, description)
VALUES

-- PCC
('TN_SOR_2025','B','B1','PCC - M5',''),
('TN_SOR_2025','B','B2','PCC - M7.5',''),
('TN_SOR_2025','B','B3','PCC - M10',''),
('TN_SOR_2025','B','B4','PCC - M15',''),
('TN_SOR_2025','B','B5','PCC - M20',''),

-- RCC
('TN_SOR_2025','C','C1','RCC - M25',''),
('TN_SOR_2025','C','C2','RCC - M30',''),
('TN_SOR_2025','C','C3','RCC - M40',''),
('TN_SOR_2025','C','C4','RCC - M50',''),

-- Reinforcement
('TN_SOR_2025','D','D1','Fe 500',''),
('TN_SOR_2025','D','D2','Fe 550',''),
('TN_SOR_2025','D','D3','Fe 550D',''),

-- Masonry
('TN_SOR_2025','E','E1','Burnt Brick (230mm X 115mm X 75mm)',''),
('TN_SOR_2025','E','E2','Cement Block (200mm X 200mm X 400mm)',''),
('TN_SOR_2025','E','E3','Cement Block (150mm X 200mm X 400mm)',''),
('TN_SOR_2025','E','E4','Cement Block (100mm X 200mm X 400mm)',''),
('TN_SOR_2025','E','E5','AAC Block (600mm X 200mm X 200mm)',''),
('TN_SOR_2025','E','E6','AAC Block (600mm X 200mm X 150mm)',''),
('TN_SOR_2025','E','E7','AAC Block (600mm X 200mm X 100mm)',''),
('TN_SOR_2025','E','E8','Flyash Block (600mm X 200mm X 100mm)',''),
('TN_SOR_2025','E','E9','Flyash Block (400mm X 200mm X 200mm)',''),
('TN_SOR_2025','E','E10','Flyash Block (230mm X 110mm X 70mm)',''),

-- Plastering
('TN_SOR_2025','F','F1','1:2 Mix',''),
('TN_SOR_2025','F','F2','1:3 Mix',''),
('TN_SOR_2025','F','F3','1:4 Mix',''),
('TN_SOR_2025','F','F4','1:5 Mix',''),
('TN_SOR_2025','F','F5','1:6 Mix',''),

-- Flooring
('TN_SOR_2025','G','G1','Marble',''),
('TN_SOR_2025','G','G2','Granite',''),
('TN_SOR_2025','G','G3','Tile',''),

-- Painting
('TN_SOR_2025','H','H1','Internal Wall',''),
('TN_SOR_2025','H','H2','External Wall',''),

-- UPVC
('TN_SOR_2025','I','I1','Doors',''),
('TN_SOR_2025','I','I2','Windows',''),

-- Fabrication
('TN_SOR_2025','J','J1','SS',''),
('TN_SOR_2025','J','J2','MS',''),
('TN_SOR_2025','J','J3','Aluminium','');

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
('Water Charges',1.00),
('Electrical Charges',1.00),
('Local Liaisoning & Dispute',0.50),
('Supervision Charges',1.00),
('Engineering & Testing Charges',0.50),
('Site Establishment',0.50),
('Insurance (Labour & Equipments)',0.50),
('Contingency, Safety Compliance & Overhead',3.00),
('Profit',9.00);

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


ALTER TABLE work_item_subpackage
ADD analysis_quantity DECIMAL(10,2),
ADD analysis_unit VARCHAR(20);

UPDATE work_item_subpackage
SET analysis_quantity = 10,
analysis_unit = 'Cu.M'
WHERE sor_code = 'TN_SOR_2025'
AND subpackage_code = 'E1';

ALTER TABLE work_item_analysis
ADD item VARCHAR(255) AFTER resource_type;

INSERT INTO work_item_analysis
(sor_code,subpackage_code,resource_type,item,material_code,labour_code,quantity,remark)
VALUES

-- MATERIAL
('TN_SOR_2025','E1','MATERIAL','Brick (500 bricks per Cu.M)','M-0003',NULL,5000,NULL),
('TN_SOR_2025','E1','MATERIAL','Cement (13.5 bags or 0.45 Cu.M)','M-0001',NULL,0.68,NULL),
('TN_SOR_2025','E1','MATERIAL','Fine Aggregate - M Sand','M-0125',NULL,2.70,NULL),

-- LABOUR
('TN_SOR_2025','E1','LABOUR','Head Mason',NULL,'L-0031',0.5,NULL),
('TN_SOR_2025','E1','LABOUR','Mason',NULL,'L-0031',10,NULL),
('TN_SOR_2025','E1','LABOUR','Male Coolie',NULL,'L-0073',7,NULL),
('TN_SOR_2025','E1','LABOUR','Female Coolie',NULL,'L-0098',10,NULL);


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
