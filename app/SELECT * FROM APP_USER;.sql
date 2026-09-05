SELECT * FROM APP_USER;

ALTER TABLE app_user
DROP CONSTRAINT IF EXISTS chk_app_user_role;

ALTER TABLE app_user
ADD CONSTRAINT chk_app_user_role
CHECK (role IN ('admin', 'manager', 'user'));
/

# JWT Admin
````
python -c "from app.services.user_service import create_user; print(create_user('admin', 'Password12345', 'admin'))"

SELECT
    conname,
    pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'app_user'::regclass;
/

CHECK (((role)::text = ANY ((ARRAY[
    'admin'::character varying, 
    'manager'::character varying, 
    'user'::character varying])::text[])))