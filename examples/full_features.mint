program init.
  var name type string.
  var age type int.
  var score type float = 0.
  var active type bool.
  var letter type char.
  var i type int = 0.
  var limit type int = 3.
initialization.
  write("Digite seu nome:").
  input(name).

  write("Digite sua idade:").
  input(age).

  write("Usuario ativo? (true/false)").
  input(active).

  write("Digite uma letra:").
  input(letter).

  move age to score.
  move score + 0.5 to score.

  while i < limit.
    log_step(i).

    if active and i < 2.
      move score + 1 to score.
    elseif not active.
      move score + 0 to score.
    else.
      move score + 2 to score.
    endif.

    i = i + 1.
  endwhile.

  move apply_bonus(score, age) to score.

  if is_adult(age).
    write("Adulto").
  else.
    write("Menor").
  endif.

  if is_letter_a(letter).
    write("Letra A").
  else.
    write("Outra letra").
  endif.

  write(name).
  write(score).
endprogram.

func log_step(step type int).
  write(step).
endfunc.

func is_adult(value type int) returns bool.
  return value >= 18.
endfunc.

func is_letter_a(ch type char) returns bool.
  return ch == 'A'.
endfunc.

func apply_bonus(base type float, years type int) returns float.
  if years >= 18.
    return base + 10.
  else.
    return base + 2.
  endif.
  return base.
endfunc.
