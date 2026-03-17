program init.
initialization.
  TRY.
    DB BEGIN.
    UPSERT INTO clients VALUES (id = 2, name = "Ana").
    DB COMMIT.
  CATCH.
    DB ROLLBACK.
  ENDTRY.
endprogram.
