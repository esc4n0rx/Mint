program init.
initialization.
  ALTER TABLE clients ADD COLUMN email string.
  ALTER TABLE clients RENAME COLUMN name TO full_name.
endprogram.
