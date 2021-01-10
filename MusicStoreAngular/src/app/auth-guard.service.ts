import { Injectable } from '@angular/core';
import { ActivatedRoute, ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot } from '@angular/router';
import { UserService } from './user.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuardService implements CanActivate{

  constructor(private userService: UserService, private router: Router) { }

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Promise<boolean> {
    return undefined;
  }

  public isLogged(): boolean {
    if (this.userService.username && !this.userService.existsButExpired()) return true;
    if (this.userService.existsButExpired()) this.userService.logout();
    this.router.navigate(['/login']);
    return false;
  }
}
