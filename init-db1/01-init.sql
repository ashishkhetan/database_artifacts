-- Create schemas
CREATE SCHEMA hr;
COMMENT ON SCHEMA hr IS 'Schema for HR-related tables';

-- Create departments table
CREATE TABLE hr.departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE hr.departments IS 'Stores department information';
COMMENT ON COLUMN hr.departments.department_id IS 'Primary key for departments';
COMMENT ON COLUMN hr.departments.department_name IS 'Name of the department';
COMMENT ON COLUMN hr.departments.location IS 'Physical location of the department';

-- Create employees table
CREATE TABLE hr.employees (
    employee_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    hire_date DATE NOT NULL,
    salary NUMERIC(10,2),
    department_id INTEGER REFERENCES hr.departments(department_id),
    manager_id INTEGER REFERENCES hr.employees(employee_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE hr.employees IS 'Stores employee information';
COMMENT ON COLUMN hr.employees.employee_id IS 'Primary key for employees';
COMMENT ON COLUMN hr.employees.first_name IS 'Employee first name';
COMMENT ON COLUMN hr.employees.last_name IS 'Employee last name';
COMMENT ON COLUMN hr.employees.email IS 'Employee email address';
COMMENT ON COLUMN hr.employees.hire_date IS 'Date when employee was hired';
COMMENT ON COLUMN hr.employees.salary IS 'Employee current salary';
COMMENT ON COLUMN hr.employees.department_id IS 'Foreign key to departments table';
COMMENT ON COLUMN hr.employees.manager_id IS 'Self-referential foreign key to employees table for manager';

-- Insert sample data
INSERT INTO hr.departments (department_name, location) VALUES
    ('Engineering', 'Building A'),
    ('Sales', 'Building B'),
    ('Marketing', 'Building B'),
    ('Human Resources', 'Building A');

INSERT INTO hr.employees (first_name, last_name, email, hire_date, salary, department_id) VALUES
    ('John', 'Doe', 'john.doe@example.com', '2020-01-15', 75000, 1),
    ('Jane', 'Smith', 'jane.smith@example.com', '2020-02-20', 85000, 1),
    ('Bob', 'Johnson', 'bob.johnson@example.com', '2020-03-10', 65000, 2),
    ('Alice', 'Williams', 'alice.williams@example.com', '2020-04-05', 70000, 3);

-- Update manager IDs
UPDATE hr.employees SET manager_id = 1 WHERE employee_id IN (2, 3);
UPDATE hr.employees SET manager_id = 2 WHERE employee_id = 4;

-- Create indexes
CREATE INDEX idx_employees_department ON hr.employees(department_id);
CREATE INDEX idx_employees_manager ON hr.employees(manager_id);
