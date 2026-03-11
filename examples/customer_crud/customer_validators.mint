FUNC validate_required(value type string) RETURNS bool.
  if value == "".
    return false.
  endif.
  return true.
ENDFUNC.

FUNC validate_email(email type string) RETURNS bool.
  if email == "".
    return false.
  endif.
  return true.
ENDFUNC.

FUNC validate_phone(phone type string) RETURNS bool.
  if phone == "".
    return false.
  endif.
  return true.
ENDFUNC.

FUNC email_already_exists(clients type table<Customer>, email type string, ignore_id type int) RETURNS bool.
  FOR customer IN clients.
    if customer.email == email and customer.id != ignore_id.
      return true.
    endif.
  ENDFOR.
  return false.
ENDFUNC.
